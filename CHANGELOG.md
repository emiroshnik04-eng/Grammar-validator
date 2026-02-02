# Changelog - История изменений проекта

## [2.1.0] - 2026-01-28

### Добавлено ✨

#### 1. Умный анализ ошибок через LLM API
- **Новый модуль `error_analyzer.py`** для автоматического анализа ошибок
- Автоматическая отправка traceback на анализ через LLM при возникновении ошибок
- Получение понятных рекомендаций по исправлению ошибок
- Интеграция с web_app.py для автоматического анализа ошибок обработки файлов

**Пример использования:**
```python
from error_analyzer import analyze_error_async

try:
    # Ваш код
    risky_operation()
except Exception as e:
    analysis = await analyze_error_async(e, context="Описание операции")
    if analysis:
        print(analysis["explanation"])
```

#### 2. Профессиональное логирование
- **Новый модуль `logging_config.py`** для настройки логов
- Логирование в файл с автоматической ротацией (максимум 10 МБ, 5 бэкапов)
- Логирование в консоль с различными уровнями (INFO, DEBUG, WARNING, ERROR)
- Замена всех `print()` на `logger.info/warning/error`

**Файл логов:** `catalog_validator.log`

**Пример:**
```python
from logging_config import logger

logger.info("Файл обработан успешно")
logger.error("Ошибка обработки", exc_info=True)
```

#### 3. Rate Limiting (защита от abuse)
- Добавлена библиотека `slowapi` для ограничения частоты запросов
- Endpoint `/api/validate` ограничен до **5 запросов в минуту** на IP
- Общий лимит **100 запросов в час** на IP
- Защита от DDoS и злоупотреблений

**Пример ответа при превышении лимита:**
```json
{
  "error": "Rate limit exceeded: 5 per 1 minute"
}
```

#### 4. Ограничение размера файлов
- Максимальный размер загружаемого файла: **100 МБ**
- Защита от исчерпания памяти и диска
- Информативное сообщение об ошибке при превышении лимита

### Исправлено 🐛

#### 1. Критическая уязвимость Path Traversal (CVE)
**Серьезность:** 🔴 CRITICAL

**До:**
```python
# Уязвимый код
file_path = os.path.join(temp_dir, filename)  # filename может быть "../../../etc/passwd"
```

**После:**
```python
# Безопасный код
safe_filename = Path(filename).name  # Берем только имя файла
file_path = temp_dir / safe_filename
file_path_resolved = file_path.resolve()

# Проверяем что путь внутри temp_dir
if not file_path_resolved.is_relative_to(temp_dir_resolved):
    raise HTTPException(status_code=403, detail="Недопустимый путь к файлу")
```

**Риск:** Злоумышленник мог получить доступ к любым файлам системы

### Улучшено 🔧

#### 1. Semantic Service (semantic_service.py)
- Добавлено логирование всех запросов к LLM API
- Улучшенная обработка ошибок с детальными сообщениями
- Обработка таймаутов и HTTP ошибок
- Логирование длины ответов от LLM

#### 2. Web App (web_app.py)
- Детальное логирование всех операций (загрузка, обработка, ошибки)
- Логирование размера загруженных файлов
- Автоматический анализ ошибок через LLM API
- Улучшенные сообщения об ошибках для пользователей

### Зависимости 📦

Добавлены в `requirements.txt`:
```
slowapi>=0.1.9  # Rate limiting
```

## Инструкции по обновлению

### 1. Установка новых зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе [.env.example](.env.example):

```bash
cp .env.example .env
```

Заполните:
```env
LLM_API_KEY=sk-your-openai-api-key-here
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4-turbo
SEMANTIC_URL=http://127.0.0.1:8000/analyze-category
```

### 3. Запуск сервисов

**Semantic Service (для умного анализа):**
```bash
python -m uvicorn semantic_service:app --host 127.0.0.1 --port 8000 --reload
```

**Web App:**
```bash
python web_app.py
```

Откройте в браузере: http://127.0.0.1:8080

### 4. Проверка логов

Логи записываются в файл `catalog_validator.log` в текущей директории.

```bash
# Просмотр последних логов
tail -f catalog_validator.log

# Поиск ошибок
grep ERROR catalog_validator.log
```

## Безопасность 🔒

### Исправленные уязвимости

1. **Path Traversal (CRITICAL)** - исправлено в [web_app.py:483-516](web_app.py#L483-L516)
2. **DoS через большие файлы (HIGH)** - добавлено ограничение 100 МБ
3. **Rate Limiting (HIGH)** - добавлена защита от abuse

### Рекомендации

- Регулярно обновляйте зависимости: `pip install --upgrade -r requirements.txt`
- Проверяйте логи на подозрительную активность
- Используйте HTTPS в продакшене
- Не храните `.env` файл в git (уже добавлен в `.gitignore`)

## Производительность 📈

### Текущие метрики

- Обработка файлов: синхронная (блокирующая)
- Максимальный размер файла: 100 МБ
- Время обработки среднего файла (10k строк): ~30 секунд
- Rate limit: 5 запросов/минуту

### Планируемые улучшения (см. IMPROVEMENTS.md)

- Асинхронная обработка файлов в фоне
- Chunked processing для больших файлов
- Кэширование результатов проверки
- WebSocket для real-time обновлений прогресса

## API Endpoints

### Web App (порт 8080)

- `GET /` - Главная страница с веб-интерфейсом
- `POST /api/validate` - Валидация CSV файла (rate limit: 5/min)
- `GET /api/download/{filename}` - Скачивание результата
- `GET /api/health` - Проверка работоспособности

### Semantic Service (порт 8000)

- `POST /analyze-category` - Анализ названия категории
- `POST /analyze-error` - Умный анализ ошибок

## Тестирование 🧪

### Тест умного анализа ошибок

```bash
python error_analyzer.py
```

### Тест логирования

```bash
python logging_config.py
```

### Запуск существующих тестов

```bash
python test_improvements.py
```

## Документация

- [README.md](README.md) - Общее описание проекта
- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [AUDIT.md](AUDIT.md) - Детальный аудит проекта
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - План будущих улучшений
- [SEMANTIC_SETUP.md](SEMANTIC_SETUP.md) - Настройка LLM сервиса

## Контрибьюторы

- Улучшения безопасности и умного анализа ошибок: Реализованы 28.01.2026

## Лицензия

См. LICENSE файл в корне проекта.
