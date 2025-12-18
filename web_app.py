"""
Веб-интерфейс для инструмента проверки каталога.
Позволяет загружать CSV файлы, запускать валидацию и скачивать результаты.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

# Импортируем логику валидации из основного скрипта
from check_catalog import process_dataframe, write_with_highlight, CONFIG


app = FastAPI(title="Catalog Validator", description="Инструмент проверки качества каталога товаров")


# HTML страница с интерфейсом
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Перевірка каталогу товарів</title>
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
        <h1>🔍 Перевірка каталогу товарів</h1>
        <p class="subtitle">Завантажте CSV файл для автоматичної перевірки якості даних</p>

        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📁</div>
            <p><strong>Натисніть для вибору файлу</strong> або перетягніть його сюди</p>
            <p style="color: #999; font-size: 14px; margin-top: 10px;">CSV файл з роздільником ";"</p>
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
            Запустити перевірку
        </button>

        <button class="btn btn-success" id="downloadBtn">
            📥 Завантажити результат
        </button>

        <div class="features">
            <h3>Що перевіряється:</h3>
            <ul>
                <li>Орфографія та граматика (LanguageTool)</li>
                <li>Множинне число категорій</li>
                <li>Розумне визначення власних імен ("Дитячий світ")</li>
                <li>Однорідність регістру в параметрах</li>
                <li>Морфологічні правила російської мови</li>
                <li>Патерн "Інший/Інше/Інша + параметр"</li>
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
                showStatus('error', 'Будь ласка, оберіть CSV файл');
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
            showStatus('processing', 'Обробка файлу... Це може зайняти кілька хвилин.');

            try {
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Помилка обробки');
                }

                const result = await response.json();
                resultFilename = result.filename;

                progressBar.classList.remove('show');
                showStatus('success', '✓ Перевірка завершена! Знайдено помилок: ' + (result.errors_found || 'N/A'));
                downloadBtn.classList.add('show');

            } catch (error) {
                progressBar.classList.remove('show');
                showStatus('error', '✗ Помилка: ' + error.message);
                processBtn.disabled = false;
            }
        });

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
async def validate_catalog(file: UploadFile = File(...)):
    """
    API endpoint для валідації завантаженого CSV файлу.
    Повертає інформацію про результати перевірки.
    """
    # Перевірка типу файлу
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Будь ласка, завантажте CSV файл")

    # Создаём временные файлы
    temp_dir = tempfile.gettempdir()
    input_path = os.path.join(temp_dir, f"input_{file.filename}")
    output_filename = f"checked_{file.filename.replace('.csv', '.xlsx')}"
    output_path = os.path.join(temp_dir, output_filename)

    try:
        # Сохраняем загруженный файл
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Читаем CSV с конфигурацией из check_catalog
        df = pd.read_csv(
            input_path,
            sep=CONFIG["sep"],
            encoding=CONFIG["encoding"],
            dtype=str
        )

        # Применяем валидацию
        df_processed = process_dataframe(df)

        # Сохраняем результат в Excel
        write_with_highlight(df_processed, output_path)

        # Подсчитываем количество ошибок (ячейки с исправлениями)
        errors_found = 0
        for col in df_processed.columns:
            if col.endswith("__correct"):
                errors_found += df_processed[col].astype(str).str.strip().ne("").sum()

        # Удаляем временный входной файл
        os.remove(input_path)

        return {
            "status": "success",
            "filename": output_filename,
            "rows_processed": len(df_processed),
            "errors_found": int(errors_found),
            "message": "Валідація завершена успішно"
        }

    except Exception as e:
        # Очистка временных файлов в случае ошибки
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

        raise HTTPException(status_code=500, detail=f"Помилка обробки файлу: {str(e)}")


@app.get("/api/download/{filename}")
async def download_result(filename: str):
    """
    API endpoint для завантаження результату перевірки.
    """
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не знайдено")

    # Перевірка безпеки: тільки файли з префіксом checked_
    if not filename.startswith("checked_"):
        raise HTTPException(status_code=403, detail="Доступ заборонено")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/api/health")
async def health_check():
    """Перевірка працездатності сервісу"""
    return {
        "status": "healthy",
        "service": "Catalog Validator",
        "version": "2.0 (UA)"
    }


if __name__ == "__main__":
    import uvicorn
    print(">>> Zapusk veb-interfeysa...")
    print(">>> Otkroyte brauzer: http://localhost:8080")
    print(">>> Ili: http://127.0.0.1:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
