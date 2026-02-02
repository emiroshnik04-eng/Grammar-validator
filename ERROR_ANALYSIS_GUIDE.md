# Руководство по умному анализу ошибок

## Обзор

Проект теперь включает **умный анализ ошибок через LLM API**. Система автоматически анализирует traceback и предоставляет понятные объяснения с рекомендациями по исправлению.

## Возможности

1. **Автоматический анализ** - Ошибки анализируются автоматически при возникновении
2. **Понятные объяснения** - LLM переводит техническийtraceback в понятное описание
3. **Рекомендации по исправлению** - Получайте конкретные шаги для решения проблемы
4. **Асинхронная работа** - Анализ не блокирует основные операции

## Настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка API ключа

Создайте файл `.env` в корне проекта:

```env
# OpenAI API ключ
LLM_API_KEY=sk-your-openai-api-key-here

# API endpoint
LLM_API_URL=https://api.openai.com/v1/chat/completions

# Модель (gpt-4-turbo рекомендуется)
LLM_MODEL=gpt-4-turbo

# URL semantic service
SEMANTIC_URL=http://127.0.0.1:8000
```

**Где получить API ключ:**
1. Зарегистрируйтесь на https://platform.openai.com
2. Перейдите в раздел API Keys
3. Создайте новый ключ
4. Скопируйте и вставьте в `.env`

### 3. Запуск Semantic Service

Semantic service должен быть запущен для анализа ошибок:

```bash
python -m uvicorn semantic_service:app --host 127.0.0.1 --port 8000 --reload
```

## Использование

### Автоматический анализ в Web App

При возникновении ошибки в web приложении, система автоматически отправит traceback на анализ:

```python
# В web_app.py
try:
    df_processed = process_dataframe(df)
except Exception as e:
    # Автоматический анализ ошибки
    error_analysis = await analyze_error_async(e, context=f"Обработка файла {file.filename}")

    # Формируем детальное сообщение
    if error_analysis and error_analysis.get("success"):
        error_detail = format_error_response(error_analysis, f"Ошибка: {str(e)}")
```

Пользователь увидит:
```
Ошибка обработки файла: KeyError: 'category_level_1_name'

💡 Умный анализ:
Проблема: В загруженном CSV файле отсутствует обязательный столбец 'category_level_1_name'.

Решение:
1. Проверьте структуру CSV файла
2. Убедитесь что присутствуют все обязательные столбцы:
   - category_level_1_name
   - category_level_2_name
   - param_name
   - value_name
3. Проверьте разделитель - должен быть точка с запятой (;)
```

### Программное использование

#### Асинхронная версия (в async функциях)

```python
from error_analyzer import analyze_error_async

async def process_data():
    try:
        # Ваш код
        result = risky_operation()
    except Exception as e:
        # Анализ ошибки
        analysis = await analyze_error_async(
            error=e,
            context="Обработка данных пользователя"
        )

        if analysis and analysis.get("success"):
            print("Объяснение:", analysis["explanation"])
            print("Тип ошибки:", analysis["error_type"])
            print("Сообщение:", analysis["error_message"])
        else:
            print("Анализ недоступен")
```

#### Синхронная версия (в обычных функциях)

```python
from error_analyzer import analyze_error_sync

def process_file(filename):
    try:
        # Ваш код
        data = load_file(filename)
    except Exception as e:
        # Синхронный анализ
        analysis = analyze_error_sync(
            error=e,
            context=f"Загрузка файла {filename}"
        )

        if analysis:
            print(analysis["explanation"])
```

### Прямой вызов API

Вы можете напрямую вызвать endpoint анализа ошибок:

```bash
curl -X POST http://127.0.0.1:8000/analyze-error \
  -H "Content-Type: application/json" \
  -d '{
    "error_traceback": "Traceback (most recent call last):\n  File \"test.py\", line 5\n    print(undefined_variable)\nNameError: name '\''undefined_variable'\'' is not defined"
  }'
```

Ответ:
```json
{
  "explanation": "## Причина ошибки\n\nВозникла ошибка `NameError`, которая означает, что вы пытаетесь использовать переменную, которая не была определена.\n\n## Решение\n\n1. Проверьте правильность написания имени переменной\n2. Убедитесь, что переменная объявлена до использования\n3. Пример исправления:\n\n```python\n# Неправильно\nprint(undefined_variable)\n\n# Правильно\nundefined_variable = \"значение\"\nprint(undefined_variable)\n```"
}
```

### Python API клиент

```python
import httpx

async def analyze_my_error(traceback_text: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8000/analyze-error",
            json={"error_traceback": traceback_text}
        )

        if response.status_code == 200:
            result = response.json()
            return result["explanation"]
        else:
            return "Ошибка анализа"
```

## Примеры анализа

### Пример 1: UnicodeDecodeError

**Traceback:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc0 in position 10
```

**Анализ LLM:**
```
Проблема: Файл был закодирован в кодировке Windows-1251, а не UTF-8.

Решение:
1. Откройте файл с правильной кодировкой:
   df = pd.read_csv('file.csv', encoding='cp1251')

2. Или конвертируйте файл в UTF-8:
   iconv -f CP1251 -t UTF-8 file.csv > file_utf8.csv
```

### Пример 2: KeyError в pandas

**Traceback:**
```
KeyError: 'column_name'
```

**Анализ LLM:**
```
Проблема: Столбец 'column_name' не найден в DataFrame.

Решение:
1. Проверьте список всех столбцов:
   print(df.columns)

2. Проверьте правильность написания имени столбца
3. Убедитесь что столбец не был удален ранее
```

### Пример 3: MemoryError

**Traceback:**
```
MemoryError: Unable to allocate 2.5 GiB
```

**Анализ LLM:**
```
Проблема: Недостаточно оперативной памяти для обработки файла.

Решение:
1. Используйте chunked reading:
   for chunk in pd.read_csv('file.csv', chunksize=10000):
       process(chunk)

2. Оптимизируйте типы данных:
   df = pd.read_csv('file.csv', dtype={'id': 'int32'})

3. Увеличьте размер swap файла
```

## Ограничения

1. **Требуется API ключ** - Без ключа анализ недоступен
2. **Лимиты OpenAI** - Учитывайте лимиты вашего аккаунта OpenAI
3. **Таймаут** - Анализ может занять до 30 секунд
4. **Стоимость** - Каждый запрос использует токены OpenAI API

## Логирование

Все запросы на анализ ошибок логируются:

```
2026-01-28 15:30:22 - catalog_validator - INFO - Получен запрос на анализ ошибки: Traceback (most recent call last)...
2026-01-28 15:30:25 - catalog_validator - INFO - Анализ ошибки выполнен успешно, длина ответа: 452 символов
```

Проверьте логи:
```bash
tail -f catalog_validator.log | grep "анализ ошибки"
```

## Отключение анализа ошибок

Если вы не хотите использовать умный анализ, просто не указывайте `LLM_API_KEY` в `.env`:

```env
# LLM_API_KEY=  # Закомментируйте эту строку
```

Приложение будет работать без анализа ошибок.

## Стоимость использования

При использовании модели **gpt-4-turbo**:
- Входные токены: $10 / 1M токенов
- Выходные токены: $30 / 1M токенов

Средний traceback: ~500 токенов
Средний ответ: ~300 токенов
**Стоимость одного анализа: ~$0.01**

Для экономии можно использовать **gpt-3.5-turbo**:
- Входные токены: $0.50 / 1M токенов
- Выходные токены: $1.50 / 1M токенов
- **Стоимость одного анализа: ~$0.0007**

Укажите в `.env`:
```env
LLM_MODEL=gpt-3.5-turbo
```

## Устранение неполадок

### Ошибка: "API ключ не настроен"

**Решение:** Создайте файл `.env` и укажите `LLM_API_KEY`

### Ошибка: "Сервис анализа ошибок недоступен"

**Решение:** Запустите semantic_service:
```bash
python -m uvicorn semantic_service:app --port 8000
```

### Ошибка: "Таймаут при обращении к LLM API"

**Решение:**
1. Проверьте интернет соединение
2. Проверьте правильность API ключа
3. Увеличьте таймаут в `error_analyzer.py`:
   ```python
   async with httpx.AsyncClient(timeout=60.0) as client:  # Было 10.0
   ```

### Ошибка: "Rate limit exceeded" от OpenAI

**Решение:**
1. Подождите несколько минут
2. Проверьте лимиты вашего аккаунта OpenAI
3. Обновите план подписки на OpenAI

## Поддержка

Если у вас возникли вопросы:
1. Проверьте логи: `catalog_validator.log`
2. Изучите [CHANGELOG.md](CHANGELOG.md) для деталей изменений
3. Создайте issue в репозитории проекта

## Дополнительная документация

- [README.md](README.md) - Общее описание проекта
- [SEMANTIC_SETUP.md](SEMANTIC_SETUP.md) - Детальная настройка LLM сервиса
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Планируемые улучшения
