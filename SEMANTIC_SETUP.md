# 🤖 Настройка Semantic Service - Пошаговая инструкция

## Что вы получите?

После настройки ваш Catalog Validator будет использовать ChatGPT для более умной проверки названий категорий.

---

## 📋 Шаг 1: Создайте файл .env

1. **Найдите файл** `.env.example` в папке проекта
2. **Скопируйте его** и переименуйте в `.env`
3. **Откройте `.env`** в любом текстовом редакторе (Блокнот, VS Code, и т.д.)

Вы увидите:
```env
LLM_API_KEY=sk-your-openai-api-key-here
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4-turbo
SEMANTIC_URL=http://127.0.0.1:8000/analyze-category
```

4. **Замените** `sk-your-openai-api-key-here` на ваш настоящий API ключ от OpenAI

Должно получиться примерно так:
```env
LLM_API_KEY=sk-proj-abc123xyz789...
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4-turbo
SEMANTIC_URL=http://127.0.0.1:8000/analyze-category
```

5. **Сохраните файл**

---

## 🚀 Шаг 2: Запустите Semantic Service

### Вариант A: Через готовый скрипт (рекомендуется)

1. **Двойной клик** по файлу `setup_semantic.bat`
2. Откроется окно терминала
3. Вы увидите:
   ```
   🚀 Запуск semantic_service...
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```
4. **НЕ ЗАКРЫВАЙТЕ это окно!** Оставьте его работать в фоне

### Вариант B: Вручную через командную строку

1. Откройте PowerShell в папке проекта
2. Выполните:
   ```powershell
   # Загрузить переменные из .env
   Get-Content .env | ForEach-Object {
       if ($_ -match '^([^#][^=]+)=(.+)$') {
           [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
       }
   }

   # Запустить сервис
   python -m uvicorn semantic_service:app --host 127.0.0.1 --port 8000 --reload
   ```
3. **НЕ ЗАКРЫВАЙТЕ это окно!**

---

## ✅ Шаг 3: Проверьте что сервис работает

1. Откройте браузер
2. Перейдите по адресу: **http://127.0.0.1:8000/docs**
3. Вы должны увидеть красивую страницу с документацией API (Swagger UI)

**Если страница открылась** — всё работает! ✅

**Если не открылась** — проверьте:
- Правильно ли вы вставили API ключ в `.env`
- Запущен ли semantic_service (смотрите окно терминала)
- Нет ли ошибок в терминале

---

## 🔍 Шаг 4: Используйте с проверкой каталога

Теперь у вас есть **ДВА способа** запуска проверки:

### Способ 1: Веб-интерфейс

1. **Оставьте semantic_service работать** (окно из Шага 2)
2. Откройте **НОВОЕ** окно PowerShell
3. Загрузите переменные:
   ```powershell
   Get-Content .env | ForEach-Object {
       if ($_ -match '^([^#][^=]+)=(.+)$') {
           [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
       }
   }
   ```
4. Запустите веб-сервер:
   ```bash
   python web_app.py
   ```
5. Откройте браузер: **http://127.0.0.1:8080**
6. Загрузите CSV и запустите проверку

### Способ 2: Командная строка

1. **Оставьте semantic_service работать**
2. Двойной клик по `run_with_semantic.bat`
3. Файл будет обработан с использованием AI

---

## 🎯 Как понять что AI работает?

При обработке файла в терминале semantic_service вы увидите запросы:

```
INFO:     127.0.0.1:52345 - "POST /analyze-category HTTP/1.1" 200 OK
INFO:     127.0.0.1:52346 - "POST /analyze-category HTTP/1.1" 200 OK
```

Это значит что check_catalog отправляет названия категорий в ChatGPT для анализа.

---

## 💰 Сколько это стоит?

При использовании `gpt-4-turbo`:
- **1 категория** ≈ $0.0001-0.0003 (сотые доли цента)
- **1000 категорий** ≈ $0.10-0.30
- **10000 категорий** ≈ $1.00-3.00

**Вывод:** Очень дёшево!

### Как снизить стоимость?

В файле `.env` измените модель на более дешёвую:
```env
LLM_MODEL=gpt-3.5-turbo  # В 10 раз дешевле, но менее точная
```

---

## 🔧 Настройка модели

В `.env` вы можете выбрать модель:

| Модель | Точность | Скорость | Цена | Рекомендация |
|--------|----------|----------|------|--------------|
| `gpt-4-turbo` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$$ | **Рекомендуется** |
| `gpt-4` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | $$$$ | Самая точная |
| `gpt-3.5-turbo` | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $ | Дешёвая |

**Совет:** Начните с `gpt-4-turbo` — это оптимальный баланс.

---

## 🛑 Как остановить semantic_service?

1. Найдите окно терминала где он запущен
2. Нажмите **Ctrl+C**
3. Сервис остановится

---

## ❓ Частые проблемы

### Проблема 1: "ModuleNotFoundError: No module named 'dotenv'"

**Решение:**
```bash
pip install python-dotenv
```

Затем в начале `semantic_service.py` и `check_catalog.py` добавьте:
```python
from dotenv import load_dotenv
load_dotenv()  # Загружает переменные из .env
```

---

### Проблема 2: "401 Unauthorized" или "Invalid API key"

**Причина:** Неправильный API ключ

**Решение:**
1. Проверьте что вы правильно скопировали ключ в `.env`
2. Убедитесь что ключ активен на https://platform.openai.com/api-keys
3. Проверьте что на аккаунте есть деньги (Billing)

---

### Проблема 3: Semantic service не запускается

**Возможные причины:**
- Порт 8000 занят другим приложением
- Не установлены зависимости

**Решение:**
```bash
# Проверить занят ли порт
netstat -ano | findstr :8000

# Если занят, измените порт в .env:
SEMANTIC_URL=http://127.0.0.1:8001/analyze-category

# И запустите на другом порту:
python -m uvicorn semantic_service:app --port 8001
```

---

### Проблема 4: Check_catalog не использует semantic service

**Проверьте:**
1. Semantic service запущен? (`http://127.0.0.1:8000/docs` открывается?)
2. Переменная `SEMANTIC_URL` установлена в терминале где запущен check_catalog?

**Проверить переменную:**
```powershell
# PowerShell
echo $env:SEMANTIC_URL

# Должно вывести: http://127.0.0.1:8000/analyze-category
```

---

## 📊 Тестирование semantic service

Хотите проверить работу AI перед обработкой файла?

1. Откройте http://127.0.0.1:8000/docs
2. Найдите endpoint `POST /analyze-category`
3. Нажмите "Try it out"
4. Вставьте тестовые данные:
   ```json
   {
     "name": "Игрушка",
     "path": "Товары > Детские товары > Игрушка"
   }
   ```
5. Нажмите "Execute"
6. Посмотрите ответ AI:
   ```json
   {
     "should_be_plural": true,
     "suggested_name": "Игрушки",
     "reason": "Категория описывает класс товаров, требуется множественное число"
   }
   ```

---

## 🎓 Полезные ссылки

- [OpenAI Platform](https://platform.openai.com/) - Управление API ключами
- [OpenAI Pricing](https://openai.com/pricing) - Тарифы
- [FastAPI Docs](https://fastapi.tiangolo.com/) - Документация фреймворка

---

## ✅ Чек-лист готовности

Перед запуском проверьте:

- [ ] Создан файл `.env` с вашим API ключом
- [ ] API ключ валидный и активный
- [ ] На OpenAI аккаунте есть деньги (Billing)
- [ ] Semantic service запущен (`http://127.0.0.1:8000/docs` открывается)
- [ ] Переменная `SEMANTIC_URL` установлена в терминале
- [ ] Всё работает! 🎉

---

**Нужна помощь?** Откройте Issue на GitHub или напишите разработчику.
