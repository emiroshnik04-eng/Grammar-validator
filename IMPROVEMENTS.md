# 🚀 План улучшений проекта Catalog Validator

**Дата создания:** 2025-01-22
**Статус:** Утверждён к реализации

---

## 📋 Краткое резюме

Этот документ содержит пошаговый план улучшений проекта Catalog Validator, разбитый на итерации с чёткими приоритетами и оценками трудозатрат.

---

## 🎯 Цели на следующий квартал

1. **Безопасность:** Устранить все критические уязвимости
2. **Качество:** Довести покрытие тестами до 80%
3. **Производительность:** Реализовать асинхронную обработку файлов
4. **Удобство:** Улучшить пользовательский опыт (UX)
5. **Масштабируемость:** Подготовить к продакшн развёртыванию

---

## 📅 Итерация 1: Критические исправления (Неделя 1-2)

### Задачи

#### 1.1. Исправить Path Traversal уязвимость 🔴 CRITICAL

**Файл:** [web_app.py:484-496](web_app.py#L484-L496)

**Проблема:** Возможность доступа к произвольным файлам системы через `../../../etc/passwd`

**Решение:**

```python
from pathlib import Path

@app.get("/api/download/{filename}")
async def download_result(filename: str):
    # Безопасная обработка имени файла
    safe_filename = Path(filename).name

    if not safe_filename.startswith("checked_"):
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    temp_dir = Path(tempfile.gettempdir())
    file_path = temp_dir / safe_filename

    # Проверка что путь внутри temp_dir
    try:
        file_path = file_path.resolve()
        if not file_path.is_relative_to(temp_dir):
            raise HTTPException(status_code=403, detail="Недопустимый путь")
    except ValueError:
        raise HTTPException(status_code=403, detail="Недопустимый путь")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(path=str(file_path), filename=safe_filename)
```

**Трудозатраты:** 1 час
**Приоритет:** КРИТИЧЕСКИЙ

---

#### 1.2. Добавить ограничение размера файлов 🟡 HIGH

**Файл:** [web_app.py:420-428](web_app.py#L420-L428)

**Решение:**

```python
from fastapi import UploadFile, File

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 МБ

@app.post("/api/validate")
async def validate_catalog(file: UploadFile = File(...)):
    # Проверка расширения
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Пожалуйста, загрузите CSV файл")

    # Чтение и проверка размера
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Файл слишком большой. Максимум {MAX_FILE_SIZE // 1024 // 1024} МБ"
        )

    # Продолжить обработку...
```

**Трудозатраты:** 30 минут
**Приоритет:** ВЫСОКИЙ

---

#### 1.3. Добавить Rate Limiting 🟡 HIGH

**Файл:** [web_app.py](web_app.py)

**Установка зависимости:**
```bash
pip install slowapi
```

**Решение:**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Инициализация
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/validate")
@limiter.limit("5/minute")  # Максимум 5 файлов в минуту
async def validate_catalog(request: Request, file: UploadFile = File(...)):
    # ... существующий код
```

**Трудозатраты:** 1 час
**Приоритет:** ВЫСОКИЙ

---

#### 1.4. Реализовать логирование 🟡 HIGH

**Новый файл:** `logging_config.py`

```python
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging():
    """Настройка логирования для приложения"""

    # Формат логов
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)

    # Файловый handler (ротация)
    file_handler = RotatingFileHandler(
        'catalog_validator.log',
        maxBytes=10*1024*1024,  # 10 МБ
        backupCount=5
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)

    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger

logger = setup_logging()
```

**Использование в коде:**

```python
import logging
logger = logging.getLogger(__name__)

# Вместо print() использовать:
logger.info("Обработка файла: %s", filename)
logger.error("Ошибка обработки: %s", str(e))
logger.debug("Найдено ошибок: %d", errors_count)
```

**Трудозатраты:** 2 часа
**Приоритет:** ВЫСОКИЙ

---

### Итого по Итерации 1:
- **Задач:** 4
- **Трудозатраты:** 4.5 часа
- **Результат:** Критические уязвимости устранены

---

## 📅 Итерация 2: Тестирование и качество (Неделя 3-4)

### Задачи

#### 2.1. Покрытие тестами > 70% 🔴 CRITICAL

**Структура тестов:**

```
tests/
├── __init__.py
├── test_check_catalog.py
├── test_web_app.py
├── test_semantic_service.py
├── test_integration.py
└── conftest.py
```

**Примеры тестов:**

**`tests/test_check_catalog.py`:**
```python
import pytest
from check_catalog import (
    ensure_category_plural,
    is_proper_noun_or_compound,
    normalize_other_pattern,
    check_case_consistency,
)

class TestCategoryPlural:
    def test_singular_to_plural(self):
        result = ensure_category_plural("Игрушка")
        assert result == ("Игрушка", "Игрушки")

    def test_already_plural(self):
        result = ensure_category_plural("Игрушки")
        assert result is None

    def test_mass_nouns(self):
        result = ensure_category_plural("транспорт")
        assert result is None

    def test_proper_nouns(self):
        result = ensure_category_plural("Детский мир")
        assert result is None

class TestProperNounDetection:
    def test_brand_with_latin(self):
        assert is_proper_noun_or_compound("iPhone 15") is True

    def test_compound_names(self):
        assert is_proper_noun_or_compound("Детский мир") is True

    def test_regular_category(self):
        assert is_proper_noun_or_compound("Игрушки") is False

class TestOtherPattern:
    def test_masculine(self):
        result = normalize_other_pattern("Цвет", "Другая цвет")
        assert result == ("Другая цвет", "Другой Цвет")

    def test_feminine(self):
        result = normalize_other_pattern("Форма", "Другой форма")
        assert result == ("Другой форма", "Другая Форма")

    def test_neuter(self):
        result = normalize_other_pattern("Качество", "Другой качество")
        assert result == ("Другой качество", "Другое Качество")
```

**`tests/test_web_app.py`:**
```python
from fastapi.testclient import TestClient
from web_app import app
import io

client = TestClient(app)

class TestHealthCheck:
    def test_health_endpoint(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

class TestFileUpload:
    def test_upload_valid_csv(self):
        csv_content = "category_level_1_name;param_name;value_name\nИгрушка;Цвет;Красный"
        file = io.BytesIO(csv_content.encode('cp1251'))

        response = client.post(
            "/api/validate",
            files={"file": ("test.csv", file, "text/csv")}
        )

        assert response.status_code == 200
        assert "filename" in response.json()

    def test_upload_invalid_extension(self):
        file = io.BytesIO(b"test content")

        response = client.post(
            "/api/validate",
            files={"file": ("test.txt", file, "text/plain")}
        )

        assert response.status_code == 400

    def test_download_security(self):
        # Попытка path traversal
        response = client.get("/api/download/../../../etc/passwd")
        assert response.status_code in [403, 404]

class TestRateLimiting:
    def test_rate_limit_exceeded(self):
        # Отправить 10 запросов быстро
        responses = []
        for _ in range(10):
            response = client.get("/api/health")
            responses.append(response.status_code)

        # Хотя бы один должен быть 429 (Too Many Requests)
        # После добавления rate limiting
        pass
```

**Запуск тестов:**
```bash
# Установка pytest
pip install pytest pytest-cov pytest-asyncio

# Запуск всех тестов
pytest tests/ -v

# С покрытием
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

**Трудозатраты:** 8 часов
**Приоритет:** КРИТИЧЕСКИЙ

---

#### 2.2. Добавить pre-commit hooks 🟢 MEDIUM

**Файл:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=127', '--extend-ignore=E203']
```

**Установка:**
```bash
pip install pre-commit
pre-commit install
```

**Трудозатраты:** 30 минут
**Приоритет:** СРЕДНИЙ

---

### Итого по Итерации 2:
- **Задач:** 2
- **Трудозатраты:** 8.5 часов
- **Результат:** Покрытие тестами > 70%, автоматические проверки кода

---

## 📅 Итерация 3: Производительность (Неделя 5-6)

### Задачи

#### 3.1. Асинхронная обработка файлов 🟡 HIGH

**Концепция:**

1. Пользователь загружает файл → получает `task_id`
2. Обработка происходит в фоне
3. Пользователь проверяет статус через `/api/status/{task_id}`
4. Когда готово → скачивает результат

**Реализация:**

**`task_manager.py`:**
```python
from typing import Dict, Optional
from enum import Enum
import uuid
from datetime import datetime

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task:
    def __init__(self, task_id: str, filename: str):
        self.task_id = task_id
        self.filename = filename
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result_filename = None
        self.error_message = None
        self.created_at = datetime.now()
        self.completed_at = None

tasks: Dict[str, Task] = {}

def create_task(filename: str) -> Task:
    task_id = str(uuid.uuid4())
    task = Task(task_id, filename)
    tasks[task_id] = task
    return task

def get_task(task_id: str) -> Optional[Task]:
    return tasks.get(task_id)
```

**Обновлённый `web_app.py`:**
```python
from fastapi import BackgroundTasks
import asyncio
from task_manager import create_task, get_task, TaskStatus

@app.post("/api/validate")
@limiter.limit("5/minute")
async def validate_catalog(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Сохранить файл
    task = create_task(file.filename)
    input_path = f"temp_{task.task_id}_{file.filename}"

    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Запустить обработку в фоне
    background_tasks.add_task(process_file_task, task.task_id, input_path)

    return {
        "task_id": task.task_id,
        "status": "processing",
        "message": "Файл принят в обработку"
    }

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": task.progress,
        "result_filename": task.result_filename,
        "error_message": task.error_message
    }

def process_file_task(task_id: str, input_path: str):
    """Фоновая обработка файла"""
    task = get_task(task_id)
    task.status = TaskStatus.PROCESSING

    try:
        # Обработка
        df = pd.read_csv(input_path, ...)
        task.progress = 30

        df_processed = process_dataframe(df)
        task.progress = 70

        output_path = f"checked_{task_id}.xlsx"
        write_with_highlight(df_processed, output_path)
        task.progress = 100

        task.status = TaskStatus.COMPLETED
        task.result_filename = output_path
        task.completed_at = datetime.now()

    except Exception as e:
        logger.error(f"Ошибка обработки задачи {task_id}: {e}")
        task.status = TaskStatus.FAILED
        task.error_message = str(e)

    finally:
        # Удалить входной файл
        if os.path.exists(input_path):
            os.remove(input_path)
```

**Обновление фронтенда:**
```javascript
// Отправка файла
const response = await fetch('/api/validate', {
    method: 'POST',
    body: formData
});

const { task_id } = await response.json();

// Проверка статуса каждые 2 секунды
const checkStatus = setInterval(async () => {
    const statusResponse = await fetch(`/api/status/${task_id}`);
    const status = await statusResponse.json();

    if (status.status === 'completed') {
        clearInterval(checkStatus);
        resultFilename = status.result_filename;
        showSuccess('Готово!');
    } else if (status.status === 'failed') {
        clearInterval(checkStatus);
        showError(status.error_message);
    } else {
        // Обновить прогресс-бар
        updateProgress(status.progress);
    }
}, 2000);
```

**Трудозатраты:** 6 часов
**Приоритет:** ВЫСОКИЙ

---

#### 3.2. Оптимизация для больших файлов 🟢 MEDIUM

**Chunked processing:**

```python
def process_large_dataframe(input_path: str, output_path: str, chunksize: int = 5000):
    """Обработка больших файлов по частям"""

    chunks_processed = []

    for chunk_num, chunk in enumerate(pd.read_csv(input_path, chunksize=chunksize)):
        logger.info(f"Обработка чанка {chunk_num + 1}")

        processed_chunk = process_dataframe(chunk)
        chunks_processed.append(processed_chunk)

    # Объединить все чанки
    final_df = pd.concat(chunks_processed, ignore_index=True)
    write_with_highlight(final_df, output_path)
```

**Трудозатраты:** 3 часа
**Приоритет:** СРЕДНИЙ

---

#### 3.3. Автоматическая очистка старых файлов 🟢 MEDIUM

**`cleanup_service.py`:**
```python
import os
import time
from pathlib import Path
import schedule
import logging

logger = logging.getLogger(__name__)

MAX_FILE_AGE_HOURS = 2

def cleanup_old_files():
    """Удалить файлы старше 2 часов из temp директории"""
    temp_dir = Path(tempfile.gettempdir())
    now = time.time()
    deleted_count = 0

    for file_path in temp_dir.glob("checked_*.xlsx"):
        file_age_hours = (now - file_path.stat().st_mtime) / 3600

        if file_age_hours > MAX_FILE_AGE_HOURS:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"Удалён старый файл: {file_path.name}")
            except Exception as e:
                logger.error(f"Ошибка удаления {file_path.name}: {e}")

    logger.info(f"Очистка завершена. Удалено файлов: {deleted_count}")

# Запуск каждый час
schedule.every(1).hours.do(cleanup_old_files)

def run_cleanup_scheduler():
    """Запустить планировщик очистки в отдельном потоке"""
    import threading

    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    logger.info("Планировщик очистки запущен")
```

**Добавить в `web_app.py`:**
```python
from cleanup_service import run_cleanup_scheduler

@app.on_event("startup")
async def startup_event():
    run_cleanup_scheduler()
    logger.info("Сервис очистки файлов запущен")
```

**Трудозатраты:** 2 часа
**Приоритет:** СРЕДНИЙ

---

### Итого по Итерации 3:
- **Задач:** 3
- **Трудозатраты:** 11 часов
- **Результат:** Асинхронная обработка, оптимизация, автоочистка

---

## 📅 Итерация 4: Docker и развёртывание (Неделя 7-8)

### Задачи

#### 4.1. Docker контейнеризация 🟡 HIGH

**`Dockerfile`:**
```dockerfile
FROM python:3.11-slim

# Установка Java для LanguageTool
RUN apt-get update && \
    apt-get install -y default-jre && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY *.py .
COPY templates/ templates/
COPY static/ static/

# Создание директории для временных файлов
RUN mkdir -p /tmp/catalog_validator

# Экспозиция порта
EXPOSE 8080

# Запуск приложения
CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8080"]
```

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_API_URL=${LLM_API_URL}
      - LLM_MODEL=${LLM_MODEL}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  semantic:
    build: .
    command: uvicorn semantic_service:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
    restart: unless-stopped
```

**`.env.example`:**
```env
LLM_API_KEY=your_openai_key_here
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4-turbo
```

**Запуск:**
```bash
# Сборка
docker-compose build

# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

**Трудозатраты:** 4 часа
**Приоритет:** ВЫСОКИЙ

---

#### 4.2. CI/CD улучшения 🟢 MEDIUM

**Добавить в `.github/workflows/ci.yml`:**
```yaml
docker-build:
  name: Docker сборка и публикация
  runs-on: ubuntu-latest
  needs: [test, lint, security]

  steps:
  - name: Checkout
    uses: actions/checkout@v4

  - name: Login to Docker Hub
    uses: docker/login-action@v3
    with:
      username: ${{ secrets.DOCKER_USERNAME }}
      password: ${{ secrets.DOCKER_PASSWORD }}

  - name: Build and push
    uses: docker/build-push-action@v5
    with:
      context: .
      push: true
      tags: yourname/catalog-validator:latest
```

**Трудозатраты:** 2 часа
**Приоритет:** СРЕДНИЙ

---

### Итого по Итерации 4:
- **Задач:** 2
- **Трудозатраты:** 6 часов
- **Результат:** Docker контейнеры, автоматическая сборка

---

## 📊 Общая сводка

| Итерация | Задач | Трудозатраты | Приоритет | Статус |
|----------|-------|--------------|-----------|--------|
| 1. Критические исправления | 4 | 4.5 ч | CRITICAL | Планируется |
| 2. Тестирование | 2 | 8.5 ч | HIGH | Планируется |
| 3. Производительность | 3 | 11 ч | HIGH | Планируется |
| 4. Docker | 2 | 6 ч | MEDIUM | Планируется |
| **ИТОГО** | **11** | **30 ч** | - | - |

---

## 🎯 Метрики успеха

После выполнения всех итераций:

- ✅ Безопасность: 0 критических уязвимостей
- ✅ Тесты: Покрытие > 80%
- ✅ Производительность: Обработка файлов в фоне
- ✅ Удобство: Прогресс-бар в реальном времени
- ✅ Развёртывание: Docker контейнеры готовы
- ✅ CI/CD: Автоматические проверки и сборка

---

## 📚 Дополнительные улучшения (Бэклог)

Низкий приоритет, можно реализовать позже:

1. **Мониторинг и алертинг**
   - Интеграция с Sentry для отслеживания ошибок
   - Prometheus метрики
   - Grafana дашборды

2. **Расширенный функционал**
   - Экспорт в JSON/PDF форматы
   - API для интеграции с другими системами
   - Пакетная обработка нескольких файлов

3. **UI/UX улучшения**
   - Тёмная тема
   - Мультиязычность (i18n)
   - Детальный просмотр ошибок в браузере

4. **Оптимизации**
   - Кэширование результатов проверки
   - CDN для статических файлов
   - Database для хранения истории проверок

---

**Следующий шаг:** Начать с Итерации 1 (критические исправления безопасности)

**Ответственный:** Разработчик проекта
**Дедлайн:** 2 недели с момента утверждения
