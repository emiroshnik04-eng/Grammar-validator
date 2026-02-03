"""
Веб-интерфейс для инструмента проверки каталога.
Позволяет загружать CSV файлы, запускать валидацию и скачивать результаты.
Включает умный анализ через LLM (OpenAI API).
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, AsyncGenerator, Dict
import logging
import json
import uuid
import asyncio

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
from pydantic import BaseModel
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем конфигурацию
try:
    from config import SERVER_HOST, SERVER_PORT, check_config, ENVIRONMENT
except ImportError:
    # Значения по умолчанию если config.py не найден
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 8080
    ENVIRONMENT = "production"
    def check_config():
        return True

# Импортируем логику валидации из основного скрипта
from check_catalog import process_dataframe, write_with_highlight, CONFIG

# Импортируем настройку логирования
from logging_config import setup_logging

# Импортируем модуль анализа ошибок
from error_analyzer import analyze_error_async, format_error_response

# Настраиваем логирование
logger = setup_logging()

# Настройки LLM
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_API_URL = os.environ.get("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4-turbo")


# Инициализация FastAPI
app = FastAPI(title="Grammar Validator", description="Инструмент проверки качества каталога товаров")

# Инициализация Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Progress tracker for SSE
progress_tracker: Dict[str, Dict] = {}


async def progress_generator(task_id: str) -> AsyncGenerator[str, None]:
    """SSE generator for real-time progress updates"""
    while True:
        if task_id not in progress_tracker:
            break
        progress = progress_tracker[task_id]
        data = json.dumps({
            "progress": progress.get("progress", 0),
            "status": progress.get("status", "processing"),
            "message": progress.get("message", "")
        })
        yield f"data: {data}\n\n"
        if progress.get("status") in ["completed", "error"]:
            break
        await asyncio.sleep(0.5)


# Модели для LLM API
class CategoryRequest(BaseModel):
    name: str
    path: str


class CategoryResponse(BaseModel):
    should_be_plural: bool
    suggested_name: str
    reason: str


class ErrorRequest(BaseModel):
    error_traceback: str


SYSTEM_PROMPT_CATEGORY = """
Ты профессиональный филолог и контент-редактор интернет-каталога.

Твоя задача — решить, как грамотно должно выглядеть название уровня
категории каталога (единственное или множественное число) и предложить
корректный вариант.

Учитывай:
- Категория описывает КЛАСС товаров (не один предмет).
- Если естественно звучит множественное число — используй его.
- Если слово по смыслу или по традиции употребляется только в единственном числе
  (клей, транспорт и т.п. в значении класса), оставь единственное.
- Сохраняй стилистику каталога, не придумывай лишние слова.

Отвечай строго JSON-объектом с полями:
- should_be_plural: true/false
- suggested_name: строка
- reason: строка с кратким пояснением.
"""

SYSTEM_PROMPT_ERROR = """
Ты опытный Python-разработчик.
Твоя задача — проанализировать текст ошибки (traceback) и дать краткое, понятное объяснение причины и способ исправления.
Отвечай структурированно, в формате Markdown.
"""


async def ask_llm_category(name: str, path: str) -> Optional[CategoryResponse]:
    """Запрашивает у LLM рекомендацию по названию категории"""
    if not LLM_API_KEY:
        return None

    prompt = (
        f"Путь категории в каталоге: {path}.\n"
        f"Текущее название уровня: {name!r}.\n"
        f"Реши, как оно должно выглядеть в финальном каталоге и нужно ли множественное число.\n"
        f"Верни JSON с полями should_be_plural, suggested_name, reason."
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                LLM_API_URL,
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json; charset=utf-8"
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_CATEGORY},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            return CategoryResponse(
                should_be_plural=bool(parsed.get("should_be_plural", False)),
                suggested_name=str(parsed.get("suggested_name", name)),
                reason=str(parsed.get("reason", "")),
            )
    except Exception as exc:
        logger.error(f"Ошибка при запросе к LLM: {exc}")
        return None


async def ask_llm_error(error_traceback: str) -> str:
    """Анализирует ошибку через LLM"""
    if not LLM_API_KEY:
        return "API ключ не настроен, я не могу проанализировать ошибку."

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                LLM_API_URL,
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json; charset=utf-8"
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_ERROR},
                        {"role": "user", "content": f"Проанализируй эту ошибку:\n\n{error_traceback}"},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.TimeoutException:
        logger.error("Превышено время ожидания при обращении к LLM API")
        return "Превышено время ожидания ответа от AI сервиса"
    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка HTTP при обращении к LLM API: {e.response.status_code}")
        return f"Ошибка связи с AI сервисом: HTTP {e.response.status_code}"
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при анализе: {str(e)}", exc_info=True)
        return f"Не удалось подключиться к AI для анализа ошибки: {e}"


# HTML page with interface
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grammar Validator</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #22CA46;
            --primary-light: #7ED321;
            --primary-dark: #43D262;
            --secondary: #8A8D93;
            --success: #56CA00;
            --error: #FF4C51;
            --warning: #FFB400;
            --info: #16B1FF;
            --background: #F4F5FA;
            --paper: #FFFFFF;
            --text-primary: rgba(58, 53, 65, 0.87);
            --text-secondary: rgba(58, 53, 65, 0.68);
            --divider: rgba(58, 53, 65, 0.12);
            --shadow-3: 0px 3px 6px rgba(58, 53, 65, 0.16), 0px 3px 6px rgba(58, 53, 65, 0.23);
            --shadow-6: 0px 6px 12px rgba(58, 53, 65, 0.18), 0px 6px 12px rgba(58, 53, 65, 0.24);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--background);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
        }

        .container {
            background: var(--paper);
            border-radius: 16px;
            box-shadow: var(--shadow-6);
            padding: 20px 24px;
            max-width: 1200px;
            width: 100%;
            display: grid;
            grid-template-columns: 1fr 320px;
            gap: 24px;
            max-height: 90vh;
        }

        .main-content {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .sidebar {
            border-left: 1px solid var(--divider);
            padding-left: 24px;
        }

        h1 {
            color: var(--text-primary);
            margin-bottom: 6px;
            font-size: 1.125rem;
            font-weight: 500;
            line-height: 1.6;
            letter-spacing: 0.15px;
        }

        .subtitle {
            color: var(--text-secondary);
            margin-bottom: 0;
            font-size: 0.875rem;
            font-weight: 400;
            line-height: 1.71;
            letter-spacing: 0.15px;
        }

        .header {
            margin-bottom: 16px;
        }

        .upload-area {
            border: 2px dashed var(--primary);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            background: rgba(34, 202, 70, 0.08);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }

        .upload-area:hover {
            border-color: var(--primary-dark);
            background: rgba(34, 202, 70, 0.12);
            transform: translateY(-2px);
        }

        .upload-area.dragover {
            border-color: var(--primary-dark);
            background: rgba(34, 202, 70, 0.16);
            transform: scale(1.01);
        }

        .upload-icon {
            font-size: 36px;
            margin-bottom: 8px;
        }

        input[type="file"] {
            display: none;
        }

        .file-info {
            background: rgba(86, 202, 0, 0.12);
            padding: 12px 16px;
            border-radius: 16px;
            display: none;
        }

        .file-info.show {
            display: block;
        }

        .file-name {
            font-weight: 500;
            color: var(--success);
            margin-bottom: 4px;
            font-size: 0.875rem;
            letter-spacing: 0.15px;
        }

        .file-size {
            color: var(--text-secondary);
            font-size: 0.75rem;
            letter-spacing: 0.4px;
        }

        .btn {
            width: 100%;
            padding: 7.5px 22px;
            border: none;
            border-radius: 50px;
            font-size: 0.9375rem;
            font-weight: 500;
            line-height: 1.71;
            letter-spacing: 0.3px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            font-family: 'Inter', sans-serif;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
            box-shadow: var(--shadow-3);
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--primary-dark);
            box-shadow: 0px 4px 8px rgba(34, 202, 70, 0.3), 0px 4px 8px rgba(34, 202, 70, 0.25);
        }

        .btn-primary:active:not(:disabled) {
            transform: translateY(1px);
            box-shadow: var(--shadow-3);
        }

        .btn-primary:disabled {
            opacity: 0.45;
            cursor: not-allowed;
            box-shadow: none;
        }

        .btn-success {
            background: var(--success);
            color: white;
            box-shadow: var(--shadow-3);
            display: none;
        }

        .btn-success.show {
            display: block;
        }

        .btn-success:hover {
            background: #4DB800;
            box-shadow: 0px 4px 8px rgba(86, 202, 0, 0.3), 0px 4px 8px rgba(86, 202, 0, 0.25);
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(58, 53, 65, 0.08);
            border-radius: 50px;
            overflow: hidden;
            display: none;
        }

        .progress-bar.show {
            display: block;
        }

        .progress-fill {
            height: 100%;
            background: var(--primary);
            width: 0%;
            transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 50px;
        }

        .progress-text {
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 12px;
            display: none;
        }

        .progress-text.show {
            display: block;
        }

        .status {
            text-align: center;
            padding: 12px 16px;
            border-radius: 16px;
            display: none;
            font-weight: 400;
            font-size: 0.875rem;
            line-height: 1.71;
            letter-spacing: 0.15px;
        }

        .status.show {
            display: block;
        }

        .status.success {
            background: rgba(86, 202, 0, 0.12);
            color: var(--success);
        }

        .status.error {
            background: rgba(255, 76, 81, 0.12);
            color: var(--error);
        }

        .status.processing {
            background: rgba(34, 202, 70, 0.12);
            color: var(--primary);
        }

        .features {
            overflow-y: auto;
            max-height: 100%;
        }

        .features h3 {
            color: var(--text-primary);
            font-size: 0.9375rem;
            font-weight: 500;
            margin-bottom: 12px;
            line-height: 1.6;
            letter-spacing: 0.15px;
        }

        .features ul {
            list-style: none;
        }

        .features li {
            padding: 5px 0;
            color: var(--text-secondary);
            font-size: 0.8125rem;
            font-weight: 400;
            line-height: 1.6;
            letter-spacing: 0.15px;
        }

        .features li:before {
            content: "✓ ";
            color: var(--success);
            font-weight: 600;
            margin-right: 8px;
        }

        .buttons-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        @media (max-width: 900px) {
            .container {
                grid-template-columns: 1fr;
                max-height: none;
            }

            .sidebar {
                border-left: none;
                border-top: 1px solid var(--divider);
                padding-left: 0;
                padding-top: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-content">
            <div class="header">
                <h1>🔍 Grammar Validator</h1>
                <p class="subtitle">Upload Excel file for automated grammar and data quality validation</p>
            </div>

            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📁</div>
                <p><strong>Click to select file</strong> or drag and drop it here</p>
                <p style="color: #999; font-size: 13px; margin-top: 8px;">Excel file (.xlsx, .xls)</p>
            </div>

            <input type="file" id="fileInput" accept=".xlsx,.xls">

            <div class="file-info" id="fileInfo">
                <div class="file-name" id="fileName"></div>
                <div class="file-size" id="fileSize"></div>
            </div>

            <div class="progress-text" id="progressText">0%</div>
            <div class="progress-bar" id="progressBar">
                <div class="progress-fill" id="progressFill"></div>
            </div>

            <div class="status" id="status"></div>

            <div class="buttons-group">
                <button class="btn btn-primary" id="processBtn" disabled>
                    Start Validation
                </button>

                <button class="btn btn-success" id="downloadBtn">
                    📥 Download Results
                </button>
            </div>
        </div>

        <div class="sidebar">
            <div class="features">
                <h3>What's validated:</h3>
                <ul>
                    <li>Spelling and grammar (LanguageTool)</li>
                    <li>Category plural forms</li>
                    <li>Smart proper noun detection ("Детский мир")</li>
                    <li>Consistent parameter capitalization</li>
                    <li>Russian language morphology rules</li>
                    <li>"Другой/Другое/Другая + parameter" pattern</li>
                    <li>Genitive case in compound parameters</li>
                    <li>First letter capitalization in categories</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const processBtn = document.getElementById('processBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const status = document.getElementById('status');

        let selectedFile = null;
        let resultFilename = null;

        // Click to upload
        uploadArea.addEventListener('click', () => fileInput.click());

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });

        // File selection
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });

        function handleFile(file) {
            const validExtensions = ['.xlsx', '.xls'];
            const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

            if (!hasValidExtension) {
                showStatus('error', 'Please select an Excel file (.xlsx or .xls)');
                return;
            }

            selectedFile = file;
            fileName.textContent = file.name;
            fileSize.textContent = formatBytes(file.size);
            fileInfo.classList.add('show');
            processBtn.disabled = false;
            downloadBtn.classList.remove('show');
            status.classList.remove('show');
        }

        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }

        function showStatus(type, message) {
            status.className = 'status show ' + type;
            status.textContent = message;
        }

        function updateProgress(percent) {
            progressFill.style.width = percent + '%';
            progressText.textContent = percent + '%';
        }

        // Process file
        processBtn.addEventListener('click', async () => {
            if (!selectedFile) return;

            const formData = new FormData();
            formData.append('file', selectedFile);

            processBtn.disabled = true;
            progressBar.classList.add('show');
            progressText.classList.add('show');
            downloadBtn.classList.remove('show');
            updateProgress(0);
            showStatus('processing', 'Processing file... This may take several minutes.');

            try {
                // Start validation
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Processing error');
                }

                const result = await response.json();
                const taskId = result.task_id;
                resultFilename = result.filename;

                // Connect to SSE for progress updates
                const eventSource = new EventSource('/api/progress/' + taskId);

                eventSource.onmessage = (event) => {
                    const data = JSON.parse(event.data);

                    // Update progress bar
                    updateProgress(data.progress);

                    // Update status message
                    if (data.message) {
                        showStatus('processing', data.message);
                    }

                    // Handle completion
                    if (data.status === 'completed') {
                        eventSource.close();
                        setTimeout(() => {
                            progressBar.classList.remove('show');
                            progressText.classList.remove('show');
                            showStatus('success', '✓ Validation completed! Errors found: ' + (result.errors_found || 'N/A'));
                            downloadBtn.classList.add('show');
                        }, 300);
                    }

                    // Handle errors
                    if (data.status === 'error') {
                        eventSource.close();
                        throw new Error(data.message || 'Processing error');
                    }
                };

                eventSource.onerror = (error) => {
                    eventSource.close();
                    // If validation completed successfully, onerror might fire on close
                    // Only show error if download button not visible
                    if (!downloadBtn.classList.contains('show')) {
                        progressBar.classList.remove('show');
                        progressText.classList.remove('show');
                        showStatus('error', '✗ Connection error during processing');
                        processBtn.disabled = false;
                    }
                };

            } catch (error) {
                progressBar.classList.remove('show');
                progressText.classList.remove('show');

                // Smart error analysis button
                const errorHtml = `
                    <div>✗ Error: ${error.message}</div>
                    <button class="btn btn-primary" style="margin-top: 10px; background: #ff9800;" onclick="analyzeError('${error.message.replace(/'/g, "\\'")}')">
                        🤖 Ask AI what this means
                    </button>
                    <div id="ai-error-explanation" style="margin-top: 10px; text-align: left; background: #fff3e0; padding: 10px; border-radius: 5px; display: none;"></div>
                `;

                status.innerHTML = errorHtml;
                status.className = 'status show error';
                processBtn.disabled = false;
            }
        });

        async function analyzeError(errorMessage) {
            const explanationBlock = document.getElementById('ai-error-explanation');
            explanationBlock.style.display = 'block';
            explanationBlock.innerHTML = 'Thinking...';

            try {
                const response = await fetch('/api/analyze-error', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({error_traceback: errorMessage})
                });
                const data = await response.json();

                // Convert markdown to simple HTML (very basic)
                let html = data.explanation || 'Failed to get explanation';
                html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                html = html.replace(/\n/g, '<br>');

                explanationBlock.innerHTML = html;
            } catch (err) {
                explanationBlock.innerHTML = 'AI service connection error: ' + err.message;
            }
        }

        // Download result
        downloadBtn.addEventListener('click', () => {
            if (!resultFilename) return;
            window.location.href = '/api/download/' + resultFilename;
        });
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница с веб-интерфейсом"""
    return HTML_TEMPLATE


@app.get("/api/progress/{task_id}")
async def stream_progress(task_id: str):
    """SSE endpoint for real-time progress updates"""
    return StreamingResponse(
        progress_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.post("/api/validate")
@limiter.limit("5/minute")
async def validate_catalog(request: Request, file: UploadFile = File(...)):
    """
    API endpoint для валидации загруженного CSV файла.
    Возвращает информацию о результатах проверки.
    Rate limit: максимум 5 запросов в минуту на IP.
    """
    # Create task ID for progress tracking
    task_id = str(uuid.uuid4())
    progress_tracker[task_id] = {"progress": 0, "status": "starting", "message": "Initializing..."}

    # Проверка типа файла
    valid_extensions = ('.xlsx', '.xls')
    if not file.filename.lower().endswith(valid_extensions):
        progress_tracker[task_id] = {"progress": 0, "status": "error", "message": "Invalid file type"}
        raise HTTPException(status_code=400, detail="Пожалуйста, загрузите Excel файл (.xlsx или .xls)")

    # Максимальный размер файла: 100 МБ
    MAX_FILE_SIZE = 100 * 1024 * 1024

    # Создаём временные файлы
    temp_dir = tempfile.gettempdir()
    input_path = os.path.join(temp_dir, f"input_{file.filename}")
    # Заменяем расширение на .xlsx для выходного файла
    base_name = file.filename.rsplit('.', 1)[0]
    output_filename = f"checked_{base_name}.xlsx"
    output_path = os.path.join(temp_dir, output_filename)

    try:
        # Читаем и проверяем размер файла
        progress_tracker[task_id] = {"progress": 10, "status": "processing", "message": "Reading file..."}
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        logger.info(f"Получен файл: {file.filename}, размер: {file_size_mb:.2f} МБ")

        if len(content) > MAX_FILE_SIZE:
            logger.warning(f"Отклонен файл {file.filename}: превышен лимит размера ({file_size_mb:.2f} МБ)")
            progress_tracker[task_id] = {"progress": 0, "status": "error", "message": "File too large"}
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024} МБ"
            )

        # Сохраняем загруженный файл
        progress_tracker[task_id] = {"progress": 20, "status": "processing", "message": "Saving file..."}
        with open(input_path, "wb") as f:
            f.write(content)

        logger.info(f"Начало обработки файла: {file.filename}")

        # Читаем Excel файл
        progress_tracker[task_id] = {"progress": 30, "status": "processing", "message": "Parsing Excel..."}
        try:
            df = pd.read_excel(
                input_path,
                dtype=str,
                engine='openpyxl' if file.filename.lower().endswith('.xlsx') else None
            )
            logger.info(f"Excel файл успешно прочитан")
        except Exception as e:
            progress_tracker[task_id] = {"progress": 0, "status": "error", "message": "Failed to parse Excel"}
            raise ValueError(f"Не удалось прочитать Excel файл: {str(e)}")

        logger.debug(f"Excel файл прочитан, строк: {len(df)}, столбцов: {len(df.columns)}")

        # Применяем валидацию
        progress_tracker[task_id] = {"progress": 50, "status": "processing", "message": "Validating data..."}
        df_processed = process_dataframe(df)

        logger.debug("Валидация завершена, сохранение результата в Excel")

        # Сохраняем результат в Excel
        progress_tracker[task_id] = {"progress": 80, "status": "processing", "message": "Saving results..."}
        write_with_highlight(df_processed, output_path)

        # Подсчитываем количество ошибок (ячейки с исправлениями)
        progress_tracker[task_id] = {"progress": 90, "status": "processing", "message": "Counting errors..."}
        errors_found = 0
        for col in df_processed.columns:
            if col.endswith("__correct"):
                errors_found += df_processed[col].astype(str).str.strip().ne("").sum()

        logger.info(f"Обработка завершена успешно. Найдено ошибок: {errors_found}, результат: {output_filename}")

        # Удаляем временный входной файл
        os.remove(input_path)

        progress_tracker[task_id] = {"progress": 100, "status": "completed", "message": "Validation completed"}

        return {
            "status": "success",
            "task_id": task_id,
            "filename": output_filename,
            "rows_processed": len(df_processed),
            "errors_found": int(errors_found),
            "message": "Валидация завершена успешно"
        }

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке файла {file.filename}: {str(e)}", exc_info=True)

        # Update progress tracker with error status
        if task_id in progress_tracker:
            progress_tracker[task_id] = {"progress": 0, "status": "error", "message": str(e)}

        # Очистка временных файлов в случае ошибки
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

        # Умный анализ ошибки через LLM
        error_analysis = await analyze_error_async(e, context=f"Обработка файла {file.filename}")

        # Формируем детальное сообщение об ошибке
        if error_analysis and error_analysis.get("success"):
            error_detail = format_error_response(error_analysis, f"Ошибка обработки файла: {str(e)}")
            logger.info("Получен умный анализ ошибки от LLM")
        else:
            error_detail = f"Ошибка обработки файла: {str(e)}"

        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/download/{filename}")
async def download_result(filename: str):
    """
    API endpoint для скачивания результата проверки.
    Защищен от Path Traversal атак.
    """
    # Безопасная обработка имени файла - берем только имя без путей
    safe_filename = Path(filename).name

    # Проверка безопасности: только файлы с префиксом checked_
    if not safe_filename.startswith("checked_"):
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    temp_dir = Path(tempfile.gettempdir())
    file_path = temp_dir / safe_filename

    # Проверка что путь внутри temp_dir (защита от path traversal)
    try:
        file_path_resolved = file_path.resolve()
        temp_dir_resolved = temp_dir.resolve()
        if not file_path_resolved.is_relative_to(temp_dir_resolved):
            raise HTTPException(status_code=403, detail="Недопустимый путь к файлу")
    except (ValueError, OSError):
        raise HTTPException(status_code=403, detail="Недопустимый путь к файлу")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(
        path=str(file_path),
        filename=safe_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/api/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy",
        "service": "Grammar Validator",
        "version": "2.0",
        "llm_enabled": bool(LLM_API_KEY)
    }


@app.post("/api/analyze-category", response_model=CategoryResponse)
async def analyze_category(req: CategoryRequest):
    """
    Умный анализ названия категории через LLM.
    Определяет нужно ли множественное число и предлагает корректный вариант.
    """
    result = await ask_llm_category(req.name, req.path)
    if result is None:
        # если LLM недоступен — вернуть "как есть"
        return CategoryResponse(
            should_be_plural=False,
            suggested_name=req.name,
            reason="LLM API не настроен или недоступен",
        )
    logger.info(f"LLM анализ категории '{req.name}': {result.suggested_name}")
    return result


@app.post("/api/analyze-error")
async def analyze_error(req: ErrorRequest):
    """
    Умный анализ ошибок через LLM API.
    Принимает traceback и возвращает понятное объяснение с решением.
    """
    traceback_preview = req.error_traceback[:100] + "..." if len(req.error_traceback) > 100 else req.error_traceback
    logger.info(f"Получен запрос на анализ ошибки: {traceback_preview}")

    explanation = await ask_llm_error(req.error_traceback)

    logger.info(f"Анализ ошибки выполнен успешно, длина ответа: {len(explanation)} символов")
    return {"explanation": explanation}


if __name__ == "__main__":
    import uvicorn
    import sys

    try:
        # Проверка конфигурации
        check_config()

        logger.info("=" * 60)
        logger.info(">>> Запуск веб-интерфейса Grammar Validator")
        logger.info(f">>> Окружение: {ENVIRONMENT}")
        logger.info("=" * 60)

        if SERVER_HOST == "0.0.0.0":
            logger.info(">>> Сервер доступен по сети!")
            logger.info(">>> Менеджеры могут подключаться по адресу:")
            logger.info(">>>   http://<IP_СЕРВЕРА>:" + str(SERVER_PORT))
            logger.info("")
            logger.info(">>> Локальный доступ:")
            logger.info(f">>>   http://127.0.0.1:{SERVER_PORT}")
        else:
            logger.info(">>> Откройте браузер и перейдите по адресу:")
            logger.info(f"   http://{SERVER_HOST}:{SERVER_PORT}")

        logger.info("")
        logger.info(">>> Для остановки сервера нажмите: Ctrl+C")
        logger.info("=" * 60)

        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info(">>> Сервер остановлен пользователем")
        logger.info("=" * 60)
        sys.exit(0)

    except OSError as e:
        if "Address already in use" in str(e) or "Обычно разрешается" in str(e):
            logger.error("\n" + "=" * 60)
            logger.error(">>> ОШИБКА: Порт 8080 уже используется!")
            logger.error(">>> Закройте другое приложение на порту 8080")
            logger.error(">>> или перезагрузите компьютер")
            logger.error("=" * 60)
            sys.exit(1)
        else:
            logger.error(f"\n>>> ОШИБКА СЕТИ: {e}")
            sys.exit(1)

    except Exception as e:
        logger.error("\n" + "=" * 60)
        logger.error(f">>> КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error(">>> Подробности в логах выше")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
