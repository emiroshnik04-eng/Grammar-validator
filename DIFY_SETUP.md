# Интеграция с Dify - Пошаговая Инструкция

## ✅ Что уже готово

Все файлы для интеграции с Dify созданы и загружены в репозитории:

- **GitHub:** https://github.com/emiroshnik04-eng/Grammar-validator
- **GitLab:** https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator

### Созданные файлы

```
dify/
├── INTEGRATION_GUIDE.md          # Подробная документация (EN + RU)
├── README.md                      # Быстрый старт
├── openapi.yaml                   # OpenAPI 3.0 спецификация
├── tool_provider.yaml             # Конфигурация провайдера инструментов
├── _assets/
│   └── validator.svg              # Иконка для Dify UI
└── tools/
    ├── validate_catalog.yaml      # Инструмент валидации каталога
    ├── suggest_category_name.yaml # Инструмент предложения названий
    └── check_health.yaml          # Проверка здоровья сервиса
```

---

## 🚀 Быстрый старт (5 минут)

### Шаг 1: Откройте Dify Admin Panel

В вашей компании Dify instance:
```
https://your-dify-domain/admin
```

### Шаг 2: Добавьте Custom Tool

1. В левом меню выберите **Tools** / **Инструменты**
2. Нажмите **Add Custom Tool** / **Добавить пользовательский инструмент**
3. Выберите **Import from OpenAPI** / **Импортировать из OpenAPI**

### Шаг 3: Импортируйте OpenAPI спецификацию

**Вариант A: Прямая ссылка (Рекомендуется)**
```
https://raw.githubusercontent.com/emiroshnik04-eng/Grammar-validator/main/dify/openapi.yaml
```

**Вариант B: Скопировать содержимое**
1. Откройте файл `dify/openapi.yaml` в репозитории
2. Скопируйте все содержимое
3. Вставьте в поле спецификации Dify

### Шаг 4: Настройте параметры

- **Name:** `Catalog Grammar Validator`
- **Author:** `Grammar Validator Team`
- **Base URL:** `https://catalog-validator.onrender.com`
- **Authentication:** `None` (или добавьте API key если настроен)

### Шаг 5: Сохраните и протестируйте

Нажмите **Save** и проверьте, что инструменты появились в списке.

---

## 🔧 Доступные инструменты

### 1. validate_catalog 📄
**Назначение:** Полная валидация CSV каталога

**Что проверяет:**
- ✅ Грамматика и орфография (LanguageTool)
- ✅ Согласование падежей (pymorphy3)
- ✅ Паттерны "Другой/Другая/Другое"
- ✅ Консистентность регистра в параметрах
- ✅ Правильность форм существительных

**Входные данные:**
- `file_content` (file) - CSV файл для валидации

**Выходные данные:**
- `task_id` - ID для отслеживания прогресса
- `message` - Статус запуска
- `status_url` - URL для проверки статуса

**Пример использования в Dify Workflow:**
```yaml
- node: upload_csv
  type: file-upload

- node: validate
  type: tool
  tool: catalog_validator.validate_catalog
  inputs:
    file_content: "{{upload_csv.file}}"
```

---

### 2. suggest_category_name 💡
**Назначение:** Анализ названий категорий с помощью LLM

**Что делает:**
- 🔍 Определяет нужна ли множественная форма
- 🏷️ Распознает собственные имена и бренды
- 📝 Предлагает правильное название с объяснением

**Входные данные:**
- `name` (string) - Название категории (например: "Игрушка")
- `path` (string) - Полный путь (например: "Детские товары / Игрушка")

**Выходные данные:**
- `should_be_plural` (boolean) - Нужна ли множественная форма
- `suggested_name` (string) - Предложенное название ("Игрушки")
- `reason` (string) - Объяснение от LLM

**Пример использования:**
```yaml
- node: analyze_category
  type: tool
  tool: catalog_validator.suggest_category_name
  inputs:
    name: "{{user_input.category_name}}"
    path: "{{user_input.category_path}}"

- node: show_result
  type: answer
  inputs:
    message: |
      Результат анализа:
      Текущее: {{user_input.category_name}}
      Правильное: {{analyze_category.suggested_name}}
      Причина: {{analyze_category.reason}}
```

---

### 3. check_health ❤️
**Назначение:** Проверка работоспособности сервиса

**Что проверяет:**
- 🟢 Статус сервиса (healthy/unhealthy)
- 🔑 Конфигурация LLM API
- 📦 Версия сервиса

**Входные данные:** Нет

**Выходные данные:**
- `status` (string) - "healthy" или "unhealthy"
- `llm_configured` (boolean) - LLM API настроен
- `version` (string) - Версия сервиса

**Рекомендуется использовать:** В начале workflow для проверки доступности

---

## 📋 Примеры Dify Applications

### Пример 1: Простой валидатор каталога

**Тип:** Workflow Application

**Описание:** Загрузить CSV → Валидировать → Скачать результаты

**Workflow:**
```yaml
nodes:
  - id: start
    type: start
    label: "Загрузите CSV файл"
    outputs: [file]

  - id: health
    type: tool
    tool: catalog_validator.check_health

  - id: validate
    type: tool
    tool: catalog_validator.validate_catalog
    inputs:
      file_content: "{{start.file}}"
    condition: "{{health.status}} == 'healthy'"

  - id: result
    type: answer
    inputs:
      message: |
        ✅ Валидация запущена!

        Task ID: {{validate.task_id}}

        Отслеживайте прогресс:
        {{validate.status_url}}
```

---

### Пример 2: Chatbot для проверки категорий

**Тип:** Chatbot Application

**System Prompt:**
```
Ты - ассистент для валидации каталогов товаров.
Помогаешь проверять правильность названий категорий на русском языке.

Используй инструмент suggest_category_name для анализа.

Формат ответа:
- Если название правильное: "✅ Название корректно"
- Если нужно исправление: "❌ Рекомендуется изменить на: [правильное название]"
- Всегда объясняй причину
```

**Пример диалога:**
```
User: Проверь категорию "Игрушка"
Bot: [Вызывает suggest_category_name]
Bot: ❌ Рекомендуется изменить на: "Игрушки"
     Причина: Названия категорий должны быть во множественном числе

User: А "Детский мир"?
Bot: [Вызывает suggest_category_name]
Bot: ✅ Название корректно: "Детский мир"
     Причина: Это собственное имя (бренд), не требует изменений
```

---

### Пример 3: Batch обработка каталогов

**Тип:** Workflow Application

**Описание:** Обработать несколько CSV файлов параллельно

**Workflow:**
```yaml
nodes:
  - id: start
    type: start
    outputs: [file_list]

  - id: loop
    type: iteration
    inputs:
      items: "{{start.file_list}}"
    children:
      - id: validate_item
        type: tool
        tool: catalog_validator.validate_catalog
        inputs:
          file_content: "{{loop.item}}"

      - id: collect
        type: variable-aggregator
        inputs:
          task_ids: "{{validate_item.task_id}}"

  - id: summary
    type: llm
    model: gpt-4
    prompt: |
      Создай отчет по валидации файлов:
      Task IDs: {{collect.task_ids}}

      Для каждого файла укажи статус и количество ошибок.
```

---

## 🔍 Тестирование интеграции

### Тест 1: Health Check

В Dify Test Console:
```
Tool: check_health
Input: (пусто)

Expected Output:
{
  "status": "healthy",
  "llm_configured": true,
  "version": "1.0.0"
}
```

### Тест 2: Category Name Suggestion

```
Tool: suggest_category_name
Input:
{
  "name": "Игрушка",
  "path": "Детские товары / Игрушка"
}

Expected Output:
{
  "should_be_plural": true,
  "suggested_name": "Игрушки",
  "reason": "Category names should be in plural form"
}
```

### Тест 3: CSV Validation

```
Tool: validate_catalog
Input:
{
  "file_content": <upload test CSV file>
}

Expected Output:
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Validation started",
  "status_url": "/api/progress/550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 📚 Дополнительная документация

### Полное руководство
Смотрите `dify/INTEGRATION_GUIDE.md` для:
- Детальных инструкций по настройке
- Примеров сложных workflow
- Troubleshooting
- Advanced configuration

### API документация
- **OpenAPI Spec:** `dify/openapi.yaml`
- **Base URL:** https://catalog-validator.onrender.com
- **Health Check:** https://catalog-validator.onrender.com/api/health

### Репозитории
- **GitHub:** https://github.com/emiroshnik04-eng/Grammar-validator
- **GitLab:** https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator

---

## ⚡ Важные замечания

### Rate Limits
- **100 requests/hour** per IP
- **10MB** max file size
- **2 minutes** timeout для валидации

### Render Free Tier
⚠️ **Важно:** Render free tier переходит в спящий режим после 15 минут неактивности.

**Первый запрос после пробуждения займет 30-60 секунд.**

Рекомендация: Используйте `check_health` в начале workflow чтобы "разбудить" сервис.

### LLM API Key
Убедитесь что `OPENAI_API_KEY` настроен в Render Environment Variables:
- Dashboard → catalog-validator → Environment
- Добавьте: `OPENAI_API_KEY = your_key_here`

---

## 🆘 Поддержка

### Проблемы с интеграцией?

1. **Проверьте health check:**
   ```bash
   curl https://catalog-validator.onrender.com/api/health
   ```

2. **Проверьте OpenAPI spec:**
   - Валиден ли YAML?
   - Правильный ли base URL?

3. **Проверьте логи Dify:**
   ```bash
   docker logs dify-api
   ```

### Создать issue
- GitHub: https://github.com/emiroshnik04-eng/Grammar-validator/issues
- GitLab: https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator/issues

---

## ✅ Checklist для внедрения

- [ ] Откройте Dify Admin Panel
- [ ] Импортируйте OpenAPI спецификацию
- [ ] Настройте tool provider
- [ ] Протестируйте все 3 инструмента
- [ ] Создайте тестовое Dify Application
- [ ] Настройте workflow/chatbot
- [ ] Протестируйте с реальными данными
- [ ] Опубликуйте приложение для команды
- [ ] Соберите feedback

---

**Готово к использованию! 🎉**

Все файлы интеграции доступны в директории `dify/` в обоих репозиториях.
