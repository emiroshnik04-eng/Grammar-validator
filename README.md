# Catalog Validator - Валидатор каталогов товаров

Единый инструмент для проверки и исправления каталогов товаров с интеграцией умного анализа через OpenAI GPT.

## 🌐 Развертывание онлайн (НОВОЕ!)

Разверните приложение в облаке БЕСПЛАТНО за 5 минут:

**Самый простой способ: [Render.com](QUICKSTART_RENDER.md)**
- Полностью бесплатно навсегда
- Автоматический деплой из GitHub
- Доступ для менеджеров по ссылке

**Другие варианты:** [Полная инструкция по облачному развертыванию](DEPLOY_CLOUD.md)

## Быстрый старт (локально)

1. **Запустите сервер**: Дважды кликните на `start.bat` или выполните `python web_app.py`
2. **Откройте браузер**: http://127.0.0.1:8080
3. **Загрузите CSV**: Выберите файл каталога
4. **Получите результат**: Скачайте проверенный Excel

## Возможности

- ✅ **Dependency parsing** - UDPipe для точного синтаксического анализа (правильно определяет "наборы кассира")
- ✅ **Real-time progress tracking** - SSE-based progress bar with live percentage updates
- ✅ **Smart filtering** - Results contain only corrected rows (no unchanged data)
- ✅ **English Material Design UI** - Modern, responsive interface with Material Design 3
- ✅ **Improved morphology** - Better compound phrase handling with head noun detection
- ✅ **Second word capitalization** - Smart handling of compound phrases (preserves proper nouns/abbreviations)
- ✅ **Орфография и грамматика** - проверка через LanguageTool
- ✅ **Умное определение множественного числа** - не преобразует "Детский мир" в "Детские миры"
- ✅ **Единообразие регистра** - проверка согласованности в рамках одного параметра
- ✅ **Морфологический анализ** - pymorphy3 для русского языка
- ✅ **LLM-анализ категорий** - опциональная семантическая проверка через OpenAI API

## 🚀 Быстрый старт

### Вариант 1: Веб-интерфейс (рекомендуется)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск веб-приложения
python web_app.py
```

Откройте браузер: **http://127.0.0.1:8080**

1. Загрузите CSV файл (разделитель `;`, кодировка `cp1251`)
2. Нажмите "Запустить проверку"
3. Скачайте результат в Excel формате

### Вариант 2: Командная строка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск проверки
python check_catalog.py
```

Настройте входной/выходной файлы в `CONFIG` внутри `check_catalog.py`.

## 📋 Требования

- **Python 3.8+**
- **Java** (для LanguageTool орфографии) - опционально
- **OpenAI API ключ** (для LLM-анализа) - опционально
- **UDPipe** (для dependency parsing) - устанавливается автоматически

### Установка Java (для орфографии)

**Windows:**
```bash
winget install Oracle.JDK.21
```

**macOS:**
```bash
brew install openjdk
```

**Linux:**
```bash
sudo apt-get install default-jre
```

Без Java скрипт будет работать, но пропустит орфографические проверки.

## 🔧 Конфигурация

### Основные настройки (check_catalog.py)

```python
CONFIG = {
    "input_file": "AZ_Игрушки_ru_RU_2025-11-18.csv",
    "output_file": "AZ_Игрушки_ru_RU_2025-11-18_checked.xlsx",
    "sep": ";",
    "encoding": "cp1251",
    "case_consistency_threshold": 0.6,  # Порог для проверки регистра (60%)
}
```

### LLM-анализ (опционально)

```bash
# Windows PowerShell
$env:LLM_API_KEY="sk-your-openai-key"
$env:LLM_API_URL="https://api.openai.com/v1/chat/completions"
$env:LLM_MODEL="gpt-4.1-mini"

# Linux/macOS
export LLM_API_KEY="sk-your-openai-key"
```

Запустите semantic service:
```bash
uvicorn semantic_service:app --reload
```

## 📊 Формат входных данных

**CSV файл** с разделителем `;` и кодировкой `cp1251`:

| Колонка | Описание |
|---------|----------|
| `category_level_1_name` ... `category_level_5_name` | Названия категорий (до 5 уровней) |
| `param_name` | Название параметра товара |
| `value_name` | Значение параметра |
| `param_id` | ID параметра (для группировки значений) |

## 📈 Формат выходных данных

**Excel файл** с результатами:

- Исходные колонки с данными
- `*__correct` - предложенное исправление
- `*__comment` - описание ошибки
- 🟠 Оранжевая подсветка ячеек с ошибками

## 🧪 Правила валидации

### 1. Категории

- **Множественное число**: "Игрушка" → "Игрушки"
- **Исключения**: имена собственные ("Детский мир"), неисчисляемые ("транспорт")
- **Орфография**: проверка через LanguageTool
- **Второе слово**: "Детские Игрушки" → "Детские игрушки" (unless proper noun/abbreviation)

### 2. Параметры

- **Единообразие регистра**: все значения в рамках `param_id` должны быть в одном регистре
- **Паттерн "Другой"**: согласование по роду/числу основного существительного ("Другой красный мяч", "Другая красная обувь")
- **Compound capitalization**: "Другой красный Цвет" → "Другой красный цвет" (preserves brands like "Другой iPhone")
- **Единственное число**: значения характеристик в единственном числе
- **Часть речи**: единообразие (прилагательные или существительные)

### 3. Умное определение имён собственных

Не преобразуются во множественное число:
- Бренды с латиницей: "Apple", "iPhone 15"
- Составные названия: "Детский мир", "Красная площадь"
- Известные места из списка `_KNOWN_PROPER_NOUNS`
- Аббревиатуры: "USB", "DVD", "LED"

### 4. Фильтрация результатов

Выходной файл содержит **только строки с ошибками**:
- Строки без исправлений автоматически исключаются
- Это ускоряет работу менеджеров по контролю качества
- Количество ошибок отображается в веб-интерфейсе

## 🛠️ API Endpoints (web_app.py)

### POST `/api/validate`
Загрузка и валидация CSV файла.

**Request:** `multipart/form-data` с полем `file`

**Response:**
```json
{
  "status": "success",
  "task_id": "uuid-here",
  "filename": "checked_file.xlsx",
  "rows_processed": 1500,
  "errors_found": 42
}
```

### GET `/api/progress/{task_id}`
Real-time progress updates via Server-Sent Events (SSE).

**Response:** Stream of SSE events
```json
{
  "progress": 50,
  "status": "processing",
  "message": "Validating data..."
}
```

### GET `/api/download/{filename}`
Скачивание результата проверки.

### GET `/api/health`
Проверка работоспособности сервиса.

## 📁 Структура проекта

```
.
├── check_catalog.py          # Основная логика валидации
├── web_app.py                # Веб-интерфейс (FastAPI)
├── semantic_service.py       # LLM-сервис для категорий
├── test_improvements.py      # Unit-тесты
├── requirements.txt          # Зависимости Python
├── openspec/                 # OpenSpec документация
│   ├── project.md           # Описание проекта
│   └── changes/             # Предложения изменений
└── README.md                # Эта документация
```

## 🧩 Расширение функционала

### Добавление известных брендов

В `check_catalog.py` найди список `_KNOWN_PROPER_NOUNS`:

```python
_KNOWN_PROPER_NOUNS = {
    "детский мир",
    "красная площадь",
    "твой новый бренд",  # Добавь сюда
}
```

### Настройка порога регистра

В `CONFIG` измени `case_consistency_threshold`:
- `0.6` = 60% значений должны совпадать (по умолчанию)
- `0.8` = 80% (более строго)
- `0.5` = 50% (более мягко)

## 🐛 Устранение проблем

### "LanguageTool не запускается"
Установите Java (см. раздел Требования). Скрипт продолжит работу без орфографии.

### "Encoding error при чтении CSV"
Убедитесь что файл в кодировке `cp1251`. Измените `encoding` в `CONFIG` если нужно.

### "Semantic service недоступен"
Это нормально - LLM-анализ опционален. Скрипт продолжит работу с локальными правилами.

## 📝 Примеры использования

### Пример 1: Быстрая проверка одного файла

```bash
# Замени имя файла в CONFIG
# CONFIG["input_file"] = "my_catalog.csv"
python check_catalog.py
```

### Пример 2: Веб-интерфейс для команды

```bash
python web_app.py
# Поделись ссылкой: http://your-ip:8080
```

### Пример 3: Batch обработка нескольких файлов

```python
import glob
from check_catalog import process_dataframe, write_with_highlight, CONFIG
import pandas as pd

for csv_file in glob.glob("data/*.csv"):
    df = pd.read_csv(csv_file, sep=";", encoding="cp1251", dtype=str)
    df_processed = process_dataframe(df)
    output = csv_file.replace(".csv", "_checked.xlsx")
    write_with_highlight(df_processed, output)
    print(f"✓ {csv_file} -> {output}")
```

## 🤝 Вклад в проект

Этот проект использует OpenSpec для управления изменениями. См. `openspec/AGENTS.md` для деталей.

## 📜 Лицензия

Проект разработан для внутреннего использования.

## 🔗 Полезные ссылки

- [pymorphy3 документация](https://pymorphy3.readthedocs.io/)
- [LanguageTool](https://languagetool.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenSpec](https://github.com/anthropics/openspec)

---

**Версия:** 3.0
**Последнее обновление:** 2026-02-02

### v3.0 Highlights (2026-02-02)
- ✨ Real-time SSE progress tracking with live percentage updates
- ✨ English Material Design UI
- ✨ Smart results filtering (only rows with errors)
- ✨ Improved second word capitalization handling
- ✨ Better "Другой" pattern morphology with head noun detection
