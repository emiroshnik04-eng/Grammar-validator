# Быстрый старт с новыми возможностями

## Обзор улучшений версии 2.1.0

Проект был значительно улучшен с добавлением:
- ✅ Исправлена критическая уязвимость Path Traversal
- ✅ Добавлено ограничение размера файлов (100 МБ)
- ✅ Добавлен Rate Limiting (защита от abuse)
- ✅ Профессиональное логирование
- ✅ Умный анализ ошибок через LLM API

## Установка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

Новые зависимости:
- `slowapi>=0.1.9` - Rate limiting

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Откройте `.env` и заполните:

```env
# OpenAI API ключ (обязательно для умного анализа ошибок)
LLM_API_KEY=sk-your-openai-api-key-here

# API endpoint (оставьте как есть)
LLM_API_URL=https://api.openai.com/v1/chat/completions

# Модель (рекомендуется gpt-4-turbo)
LLM_MODEL=gpt-4-turbo

# URL semantic service (оставьте как есть)
SEMANTIC_URL=http://127.0.0.1:8000
```

**Где получить API ключ OpenAI:**
1. Зарегистрируйтесь на https://platform.openai.com
2. Перейдите в API Keys
3. Создайте новый ключ
4. Скопируйте и вставьте в `.env`

## Запуск

### Вариант 1: Только Web App (без умного анализа)

Если вы не хотите использовать умный анализ ошибок:

```bash
python web_app.py
```

Откройте браузер: http://127.0.0.1:8080

### Вариант 2: С умным анализом ошибок (рекомендуется)

Запустите два сервиса:

**Терминал 1 - Semantic Service:**
```bash
python -m uvicorn semantic_service:app --host 127.0.0.1 --port 8000 --reload
```

**Терминал 2 - Web App:**
```bash
python web_app.py
```

Откройте браузер: http://127.0.0.1:8080

## Быстрая проверка новых возможностей

### 1. Проверка логирования

```bash
# Запустите приложение
python web_app.py

# В другом терминале наблюдайте за логами
tail -f catalog_validator.log
```

Вы увидите:
```
2026-01-28 15:30:00 - catalog_validator - INFO - ==========================================
2026-01-28 15:30:00 - catalog_validator - INFO - 🚀 Запуск веб-интерфейса Catalog Validator
2026-01-28 15:30:00 - catalog_validator - INFO - ==========================================
```

### 2. Проверка Rate Limiting

Откройте консоль разработчика в браузере и выполните:

```javascript
// Отправить 10 запросов быстро
for (let i = 0; i < 10; i++) {
  fetch('/api/health')
    .then(r => r.json())
    .then(d => console.log(i, d))
    .catch(e => console.error(i, e));
}
```

После 5-го запроса получите:
```json
{
  "error": "Rate limit exceeded: 5 per 1 minute"
}
```

### 3. Проверка ограничения размера файлов

Попробуйте загрузить файл больше 100 МБ. Увидите:
```
Файл слишком большой. Максимальный размер: 100 МБ
```

### 4. Проверка Path Traversal защиты

Попробуйте обратиться к:
```
http://127.0.0.1:8080/api/download/../../../etc/passwd
```

Получите:
```json
{
  "detail": "Доступ запрещён"
}
```

### 5. Проверка умного анализа ошибок

**Способ 1: Через Python**

```bash
python error_analyzer.py
```

**Способ 2: Через API**

```bash
curl -X POST http://127.0.0.1:8000/analyze-error \
  -H "Content-Type: application/json" \
  -d '{
    "error_traceback": "Traceback (most recent call last):\n  File \"test.py\", line 5\n    result = 10 / 0\nZeroDivisionError: division by zero"
  }'
```

Получите детальный анализ от LLM.

**Способ 3: Загрузить некорректный CSV**

1. Создайте файл `bad.csv` с неправильной структурой
2. Загрузите через веб-интерфейс
3. Получите ошибку с умным анализом:

```
Ошибка обработки файла: KeyError: 'category_level_1_name'

💡 Умный анализ:
Проблема: В CSV файле отсутствует обязательный столбец 'category_level_1_name'.

Решение:
1. Проверьте структуру CSV файла
2. Убедитесь что присутствуют все обязательные столбцы
3. Проверьте разделитель - должен быть точка с запятой (;)
```

## Типичные сценарии использования

### Сценарий 1: Обработка CSV файла

1. Откройте http://127.0.0.1:8080
2. Перетащите CSV файл или нажмите для выбора
3. Нажмите "Запустить проверку"
4. Дождитесь обработки
5. Скачайте результат в Excel

**Логи покажут:**
```
INFO - Получен файл: catalog.csv, размер: 2.34 МБ
INFO - Начало обработки файла: catalog.csv
DEBUG - CSV файл прочитан, строк: 15000, столбцов: 8
DEBUG - Валидация завершена, сохранение результата в Excel
INFO - Обработка завершена успешно. Найдено ошибок: 234
```

### Сценарий 2: Отладка ошибки с LLM

```python
import asyncio
from error_analyzer import analyze_error_async

async def test_analysis():
    try:
        # Ваш код с ошибкой
        data = {"key": "value"}
        result = data["missing_key"]
    except KeyError as e:
        analysis = await analyze_error_async(
            e,
            context="Попытка доступа к словарю"
        )

        if analysis:
            print("=== УМНЫЙ АНАЛИЗ ===")
            print(analysis["explanation"])

asyncio.run(test_analysis())
```

### Сценарий 3: Мониторинг логов в реальном времени

```bash
# Linux/Mac
tail -f catalog_validator.log | grep ERROR

# Windows (PowerShell)
Get-Content catalog_validator.log -Wait | Select-String "ERROR"
```

## Производительность

### Текущие метрики

| Метрика | Значение |
|---------|----------|
| Максимальный размер файла | 100 МБ |
| Rate limit (валидация) | 5 запросов/минуту |
| Rate limit (общий) | 100 запросов/час |
| Среднее время обработки (10k строк) | ~30 секунд |
| Время анализа ошибки через LLM | ~3 секунды |

### Рекомендации

- Для файлов > 50 МБ ожидайте обработку 5-10 минут
- Умный анализ ошибок занимает 3-5 секунд (асинхронно)
- Логи ротируются автоматически (максимум 10 МБ × 5 файлов)

## Устранение неполадок

### Проблема: "ModuleNotFoundError: No module named 'slowapi'"

**Решение:**
```bash
pip install slowapi
# или
pip install -r requirements.txt
```

### Проблема: "LLM API ключ не настроен"

**Решение:**
1. Создайте файл `.env`
2. Добавьте `LLM_API_KEY=sk-...`
3. Перезапустите приложение

### Проблема: "Сервис анализа ошибок недоступен"

**Решение:**
Запустите semantic service:
```bash
python -m uvicorn semantic_service:app --port 8000
```

### Проблема: Логи не записываются

**Проверка:**
```bash
# Проверьте права на запись
ls -la catalog_validator.log

# Windows
icacls catalog_validator.log
```

**Решение:**
```bash
# Создайте файл вручную
touch catalog_validator.log

# Windows
echo. > catalog_validator.log
```

### Проблема: Rate limit слишком строгий

**Решение:**
Отредактируйте `web_app.py`:
```python
# Было:
@limiter.limit("5/minute")

# Станет (например, 10 запросов в минуту):
@limiter.limit("10/minute")
```

## Тестирование

### Юнит-тесты

```bash
python test_improvements.py
```

### Тест логирования

```bash
python logging_config.py
```

### Тест анализа ошибок

```bash
python error_analyzer.py
```

### Интеграционный тест

1. Запустите оба сервиса (web_app + semantic_service)
2. Загрузите тестовый CSV файл
3. Проверьте логи: `tail -f catalog_validator.log`
4. Проверьте результат в Excel файле

## Дополнительные ресурсы

- [CHANGELOG.md](CHANGELOG.md) - История изменений
- [ERROR_ANALYSIS_GUIDE.md](ERROR_ANALYSIS_GUIDE.md) - Детальное руководство по умному анализу
- [AUDIT.md](AUDIT.md) - Аудит проекта
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Планируемые улучшения

## Безопасность

### Что было исправлено

1. **Path Traversal (CRITICAL)** - теперь невозможно получить доступ к системным файлам
2. **DoS через большие файлы** - ограничение 100 МБ
3. **Rate Limiting** - защита от злоупотреблений

### Рекомендации

- Не храните `.env` в git
- Регулярно обновляйте зависимости
- Проверяйте логи на подозрительную активность
- Используйте HTTPS в продакшене

## Поддержка

Если возникли проблемы:
1. Проверьте логи: `catalog_validator.log`
2. Изучите документацию в репозитории
3. Создайте issue с описанием проблемы

## Лицензия

См. LICENSE файл в корне проекта.
