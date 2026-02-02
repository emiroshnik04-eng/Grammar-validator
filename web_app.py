"""
Веб-интерфейс для инструмента проверки каталога.
Позволяет загружать CSV файлы, запускать валидацию и скачивать результаты.
Включает умный анализ через LLM (OpenAI API).
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
import logging
import json

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
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
app = FastAPI(title="Catalog Validator", description="Инструмент проверки качества каталога товаров")

# Инициализация Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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


# HTML страница с интерфейсом
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Проверка каталога товаров</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 40px 20px;
            text-align: center;
            background: #f8f9ff;
            transition: all 0.3s ease;
            cursor: pointer;
            margin-bottom: 20px;
        }

        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f1ff;
        }

        .upload-area.dragover {
            border-color: #764ba2;
            background: #e8e9ff;
            transform: scale(1.02);
        }

        .upload-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }

        input[type="file"] {
            display: none;
        }

        .file-info {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }

        .file-info.show {
            display: block;
        }

        .file-name {
            font-weight: 600;
            color: #2e7d32;
            margin-bottom: 5px;
        }

        .file-size {
            color: #666;
            font-size: 14px;
        }

        .btn {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 10px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }

        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-success {
            background: #4caf50;
            color: white;
            display: none;
        }

        .btn-success.show {
            display: block;
        }

        .btn-success:hover {
            background: #45a049;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(76, 175, 80, 0.4);
        }

        .progress-bar {
            width: 100%;
            height: 6px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 20px;
            display: none;
        }

        .progress-bar.show {
            display: block;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s ease;
            animation: progress 2s ease-in-out infinite;
        }

        @keyframes progress {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(400%); }
        }

        .status {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }

        .status.show {
            display: block;
        }

        .status.success {
            background: #e8f5e9;
            color: #2e7d32;
        }

        .status.error {
            background: #ffebee;
            color: #c62828;
        }

        .status.processing {
            background: #e3f2fd;
            color: #1565c0;
        }

        .features {
            margin-top: 30px;
            padding-top: 30px;
            border-top: 1px solid #e0e0e0;
        }

        .features h3 {
            color: #333;
            font-size: 16px;
            margin-bottom: 15px;
        }

        .features ul {
            list-style: none;
        }

        .features li {
            padding: 8px 0;
            color: #666;
            font-size: 14px;
        }

        .features li:before {
            content: "✓ ";
            color: #4caf50;
            font-weight: bold;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Проверка каталога товаров</h1>
        <p class="subtitle">Загрузите CSV файл для автоматической проверки качества данных</p>

        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📁</div>
            <p><strong>Нажмите для выбора файла</strong> или перетащите его сюда</p>
            <p style="color: #999; font-size: 14px; margin-top: 10px;">CSV файл с разделителем ";"</p>
        </div>

        <input type="file" id="fileInput" accept=".csv">

        <div class="file-info" id="fileInfo">
            <div class="file-name" id="fileName"></div>
            <div class="file-size" id="fileSize"></div>
        </div>

        <div class="progress-bar" id="progressBar">
            <div class="progress-fill"></div>
        </div>

        <div class="status" id="status"></div>

        <button class="btn btn-primary" id="processBtn" disabled>
            Запустить проверку
        </button>

        <button class="btn btn-success" id="downloadBtn">
            📥 Скачать результат
        </button>

        <div class="features">
            <h3>Что проверяется:</h3>
            <ul>
                <li>Орфография и грамматика (LanguageTool)</li>
                <li>Множественное число категорий</li>
                <li>Умное определение имён собственных ("Детский мир")</li>
                <li>Единообразие регистра в параметрах</li>
                <li>Морфологические правила русского языка</li>
                <li>Паттерн "Другой/Другое/Другая + параметр"</li>
            </ul>
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
            if (!file.name.endsWith('.csv')) {
                showStatus('error', 'Пожалуйста, выберите CSV файл');
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

        // Process file
        processBtn.addEventListener('click', async () => {
            if (!selectedFile) return;

            const formData = new FormData();
            formData.append('file', selectedFile);

            processBtn.disabled = true;
            progressBar.classList.add('show');
            downloadBtn.classList.remove('show');
            showStatus('processing', 'Обработка файла... Это может занять несколько минут.');

            try {
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Ошибка обработки');
                }

                const result = await response.json();
                resultFilename = result.filename;

                progressBar.classList.remove('show');
                showStatus('success', '✓ Проверка завершена! Найдено ошибок: ' + (result.errors_found || 'N/A'));
                downloadBtn.classList.add('show');

            } catch (error) {
                progressBar.classList.remove('show');
                
                // Кнопка умного поиска ошибки
                const errorHtml = `
                    <div>✗ Ошибка: ${error.message}</div>
                    <button class="btn btn-primary" style="margin-top: 10px; background: #ff9800;" onclick="analyzeError('${error.message.replace(/'/g, "\\'")}')">
                        🤖 Спросить AI что это значит
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
                const response = await fetch('http://127.0.0.1:8000/analyze-error', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({error_traceback: errorMessage})
                });
                const data = await response.json();
                
                // Преобразуем markdown в простой HTML (очень базово)
                let html = data.explanation || 'Не удалось получить объяснение';
                html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                html = html.replace(/\n/g, '<br>');
                
                explanationBlock.innerHTML = html;
            } catch (err) {
                explanationBlock.innerHTML = 'Ошибка связи с AI сервисом: ' + err.message;
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


@app.post("/api/validate")
@limiter.limit("5/minute")
async def validate_catalog(request: Request, file: UploadFile = File(...)):
    """
    API endpoint для валидации загруженного CSV файла.
    Возвращает информацию о результатах проверки.
    Rate limit: максимум 5 запросов в минуту на IP.
    """
    # Проверка типа файла
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Пожалуйста, загрузите CSV файл")

    # Максимальный размер файла: 100 МБ
    MAX_FILE_SIZE = 100 * 1024 * 1024

    # Создаём временные файлы
    temp_dir = tempfile.gettempdir()
    input_path = os.path.join(temp_dir, f"input_{file.filename}")
    output_filename = f"checked_{file.filename.replace('.csv', '.xlsx')}"
    output_path = os.path.join(temp_dir, output_filename)

    try:
        # Читаем и проверяем размер файла
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        logger.info(f"Получен файл: {file.filename}, размер: {file_size_mb:.2f} МБ")

        if len(content) > MAX_FILE_SIZE:
            logger.warning(f"Отклонен файл {file.filename}: превышен лимит размера ({file_size_mb:.2f} МБ)")
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024} МБ"
            )

        # Сохраняем загруженный файл
        with open(input_path, "wb") as f:
            f.write(content)

        logger.info(f"Начало обработки файла: {file.filename}")

        # Читаем CSV с автоматическим определением кодировки
        encodings_to_try = ["utf-8", "utf-8-sig", "cp1251", "windows-1251", "latin-1", "iso-8859-1"]
        df = None
        last_error = None

        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(
                    input_path,
                    sep=CONFIG["sep"],
                    encoding=encoding,
                    dtype=str
                )
                logger.info(f"CSV файл успешно прочитан с кодировкой: {encoding}")
                break
            except Exception as e:
                last_error = e
                logger.debug(f"Попытка чтения с кодировкой {encoding} не удалась: {type(e).__name__}")
                continue

        if df is None:
            raise ValueError(f"Не удалось прочитать файл ни с одной из кодировок: {encodings_to_try}. Последняя ошибка: {last_error}")

        logger.debug(f"CSV файл прочитан, строк: {len(df)}, столбцов: {len(df.columns)}")

        # Применяем валидацию
        df_processed = process_dataframe(df)

        logger.debug("Валидация завершена, сохранение результата в Excel")

        # Сохраняем результат в Excel
        write_with_highlight(df_processed, output_path)

        # Подсчитываем количество ошибок (ячейки с исправлениями)
        errors_found = 0
        for col in df_processed.columns:
            if col.endswith("__correct"):
                errors_found += df_processed[col].astype(str).str.strip().ne("").sum()

        logger.info(f"Обработка завершена успешно. Найдено ошибок: {errors_found}, результат: {output_filename}")

        # Удаляем временный входной файл
        os.remove(input_path)

        return {
            "status": "success",
            "filename": output_filename,
            "rows_processed": len(df_processed),
            "errors_found": int(errors_found),
            "message": "Валидация завершена успешно"
        }

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке файла {file.filename}: {str(e)}", exc_info=True)

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
        "service": "Catalog Validator",
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
        logger.info(">>> Запуск веб-интерфейса Catalog Validator")
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
