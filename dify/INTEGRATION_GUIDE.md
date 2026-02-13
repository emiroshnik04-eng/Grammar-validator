# Dify Integration Guide
# Руководство по интеграции с Dify

## Overview / Обзор

Этот проект интегрируется с Dify как Custom Tool Provider, позволяя использовать валидацию каталогов внутри Dify workflows и applications.

This project integrates with Dify as a Custom Tool Provider, enabling catalog validation within Dify workflows and applications.

---

## Prerequisites / Требования

- ✅ Доступ к Dify instance (cloud или self-hosted)
- ✅ Права администратора для добавления Custom Tools
- ✅ Валидатор развернут и доступен по URL (https://catalog-validator.onrender.com)

---

## Installation Steps / Шаги установки

### Option 1: Import via OpenAPI Spec (Recommended)

#### 1. Open Dify Admin Panel
Откройте панель администратора Dify:
- Cloud: https://cloud.dify.ai/admin
- Self-hosted: `https://your-dify-domain/admin`

#### 2. Navigate to Tools
1. В боковом меню выберите **Tools** / **Инструменты**
2. Нажмите **Add Custom Tool** / **Добавить пользовательский инструмент**
3. Выберите **Import from OpenAPI** / **Импортировать из OpenAPI**

#### 3. Import OpenAPI Specification
1. Скопируйте содержимое файла `dify/openapi.yaml`
2. Вставьте в поле спецификации
3. Или укажите URL: `https://raw.githubusercontent.com/emiroshnik04-eng/Grammar-validator/main/dify/openapi.yaml`

#### 4. Configure Tool
- **Name:** Catalog Grammar Validator
- **Author:** Grammar Validator Team
- **Base URL:** `https://catalog-validator.onrender.com`
- **Authentication:** None (можно добавить API key если настроен)

#### 5. Test the Tool
Протестируйте инструмент:
```json
{
  "name": "Игрушка",
  "path": "Детские товары / Игрушка"
}
```

Expected output:
```json
{
  "should_be_plural": true,
  "suggested_name": "Игрушки",
  "reason": "Названия категорий должны быть во множественном числе"
}
```

---

### Option 2: Manual Tool Provider Setup

#### 1. Create Tool Provider Directory
В вашем Dify instance создайте структуру:
```
dify/
└── tools/
    └── catalog_validator/
        ├── _assets/
        │   └── validator.svg
        ├── tools/
        │   ├── validate_catalog.yaml
        │   ├── suggest_category_name.yaml
        │   └── check_health.yaml
        └── catalog_validator.yaml
```

#### 2. Copy Configuration Files
Скопируйте все файлы из `dify/` в соответствующие директории.

#### 3. Register Tool Provider
В Dify:
1. Tools → Add Provider → Local Provider
2. Укажите путь к `catalog_validator.yaml`
3. Сохраните

---

## Available Tools / Доступные инструменты

### 1. validate_catalog
**Назначение:** Валидация CSV файла каталога

**Входные параметры:**
- `file_path` (string): Путь к CSV файлу
- `file_content` (file): Или прямая загрузка файла

**Выходные данные:**
- `task_id` (string): ID задачи для отслеживания
- `message` (string): Статусное сообщение
- `status_url` (string): URL для проверки статуса

**Пример использования в workflow:**
```yaml
- node: validate_catalog
  inputs:
    file_path: "{{uploaded_file_path}}"
  outputs:
    task_id: "{{validate_catalog.task_id}}"
```

---

### 2. suggest_category_name
**Назначение:** Анализ и предложение правильного названия категории

**Входные параметры:**
- `name` (string): Название категории
- `path` (string): Полный путь категории

**Выходные данные:**
- `should_be_plural` (boolean): Должно ли быть во множественном числе
- `suggested_name` (string): Предложенное название
- `reason` (string): Объяснение от LLM

**Пример использования:**
```yaml
- node: suggest_category_name
  inputs:
    name: "Игрушка"
    path: "Детские товары / Игрушка"
  outputs:
    suggestion: "{{suggest_category_name.suggested_name}}"
```

---

### 3. check_health
**Назначение:** Проверка работоспособности сервиса

**Входные параметры:** Нет

**Выходные данные:**
- `status` (string): healthy/unhealthy
- `llm_configured` (boolean): LLM настроен
- `version` (string): Версия сервиса

---

## Example Workflows / Примеры workflow

### Workflow 1: Simple Catalog Validation

```yaml
name: "Validate Catalog"
description: "Upload CSV and validate Russian grammar"

nodes:
  - id: start
    type: start
    outputs:
      - file_upload

  - id: health_check
    type: tool
    tool: catalog_validator.check_health
    inputs: {}

  - id: validate
    type: tool
    tool: catalog_validator.validate_catalog
    inputs:
      file_content: "{{start.file_upload}}"
    condition:
      - "{{health_check.status}} == 'healthy'"

  - id: result
    type: end
    inputs:
      task_id: "{{validate.task_id}}"
      message: "Validation started. Check status at: {{validate.status_url}}"
```

---

### Workflow 2: Category Name Validator with Suggestions

```yaml
name: "Category Name Validator"
description: "Analyze category names and suggest corrections"

nodes:
  - id: start
    type: start
    outputs:
      - category_name
      - category_path

  - id: suggest
    type: tool
    tool: catalog_validator.suggest_category_name
    inputs:
      name: "{{start.category_name}}"
      path: "{{start.category_path}}"

  - id: decision
    type: if-else
    condition: "{{suggest.should_be_plural}} == true"
    branches:
      - true:
          - id: needs_plural
            type: answer
            inputs:
              message: |
                ❌ Название категории должно быть во множественном числе.

                Текущее: {{start.category_name}}
                Правильное: {{suggest.suggested_name}}

                Причина: {{suggest.reason}}
      - false:
          - id: correct
            type: answer
            inputs:
              message: |
                ✅ Название категории корректно: {{start.category_name}}
```

---

### Workflow 3: Batch Catalog Processing

```yaml
name: "Batch Catalog Validation"
description: "Process multiple catalogs and aggregate results"

nodes:
  - id: start
    type: start
    outputs:
      - file_list

  - id: loop
    type: iteration
    inputs:
      items: "{{start.file_list}}"
    children:
      - id: validate_item
        type: tool
        tool: catalog_validator.validate_catalog
        inputs:
          file_path: "{{loop.item}}"

      - id: collect_results
        type: variable-aggregator
        inputs:
          task_ids: "{{validate_item.task_id}}"

  - id: summary
    type: llm
    model: gpt-4
    prompt: |
      Проанализируй результаты валидации:
      Task IDs: {{collect_results.task_ids}}

      Создай краткий отчет по всем валидациям.
```

---

## Creating Dify Application / Создание Dify приложения

### Step 1: Create Application
1. В Dify перейдите в **Studio**
2. Нажмите **Create Application**
3. Выберите тип: **Workflow** или **Chatbot**

### Step 2: Configure Interface
Для Workflow приложения:
- **Input:** File upload (CSV)
- **Output:** Validation results

Для Chatbot:
- **System Prompt:**
```
Ты - ассистент для валидации каталогов товаров.
Помогаешь пользователям проверять грамматику и согласование в CSV файлах.
Используй инструменты catalog_validator для анализа.
```

### Step 3: Add Tools
1. В workflow editor добавьте ноды с нашими tools
2. Подключите входы и выходы
3. Настройте условную логику (if-else) при необходимости

### Step 4: Test Application
1. Нажмите **Preview**
2. Загрузите тестовый CSV файл
3. Проверьте результаты валидации

### Step 5: Publish
1. Нажмите **Publish**
2. Получите публичную ссылку на приложение
3. Поделитесь с пользователями

---

## API Endpoints Reference

### Base URL
```
https://catalog-validator.onrender.com
```

### Endpoints

#### POST /api/validate
Загрузить CSV для валидации
```bash
curl -X POST "https://catalog-validator.onrender.com/api/validate" \
  -F "file=@catalog.csv"
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Validation started"
}
```

#### GET /api/validate/result/{task_id}
Получить результат валидации
```bash
curl "https://catalog-validator.onrender.com/api/validate/result/{task_id}"
```

Response:
```json
{
  "status": "completed",
  "progress": 100,
  "errors_found": 15,
  "result_url": "/download/{task_id}"
}
```

#### POST /suggest-category-name
Предложить название категории
```bash
curl -X POST "https://catalog-validator.onrender.com/suggest-category-name" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Игрушка",
    "path": "Детские товары / Игрушка"
  }'
```

Response:
```json
{
  "should_be_plural": true,
  "suggested_name": "Игрушки",
  "reason": "Category names should be in plural form"
}
```

#### GET /api/health
Проверка работоспособности
```bash
curl "https://catalog-validator.onrender.com/api/health"
```

Response:
```json
{
  "status": "healthy",
  "llm_configured": true,
  "version": "1.0.0"
}
```

---

## Troubleshooting / Решение проблем

### Issue 1: Tool not appearing in Dify
**Problem:** Custom tool не отображается в списке

**Solution:**
1. Проверьте формат YAML файлов
2. Убедитесь, что OpenAPI spec валиден
3. Перезагрузите Dify (если self-hosted)
4. Проверьте логи: `docker logs dify-api`

### Issue 2: Authentication errors
**Problem:** 401 Unauthorized

**Solution:**
1. Проверьте, что API key настроен правильно
2. Добавьте API key в Dify tool credentials
3. Убедитесь, что Render service имеет доступ к OPENAI_API_KEY

### Issue 3: File upload fails
**Problem:** Ошибка при загрузке CSV файла

**Solution:**
1. Проверьте размер файла (лимит: 10MB)
2. Убедитесь, что файл в формате CSV UTF-8
3. Проверьте rate limits (100 requests/hour)

### Issue 4: Validation takes too long
**Problem:** Валидация не завершается

**Solution:**
1. Проверьте статус через `/api/validate/result/{task_id}`
2. Render free tier может спать - первый запрос займет 30-60 сек
3. Используйте SSE endpoint для real-time прогресса

---

## Advanced Configuration / Расширенная настройка

### Custom Environment Variables in Dify

Если вы используете self-hosted Dify, можете добавить переменные окружения:

```yaml
# docker-compose.yml
services:
  api:
    environment:
      - CATALOG_VALIDATOR_URL=https://catalog-validator.onrender.com
      - CATALOG_VALIDATOR_API_KEY=your_api_key_here
```

### Rate Limiting

Текущие лимиты:
- 100 requests per hour per IP
- 10MB max file size
- 2 минуты timeout для validation

Для увеличения лимитов обратитесь к администратору.

---

## Support / Поддержка

### Documentation
- OpenAPI Spec: `/dify/openapi.yaml`
- Tool Configs: `/dify/tools/`

### Issues
- GitHub: https://github.com/emiroshnik04-eng/Grammar-validator/issues
- GitLab: https://gitlab.lalafo.com.ua/ekaterina.miroshnik/catalog-grammar-validator/issues

### Validator URL
- Production: https://catalog-validator.onrender.com

---

## Next Steps / Следующие шаги

1. ✅ Импортируйте OpenAPI spec в Dify
2. ✅ Создайте тестовое Dify приложение
3. ✅ Настройте workflow с инструментами валидации
4. ✅ Опубликуйте приложение для команды
5. ✅ Соберите feedback от пользователей

---

**Успешной интеграции! 🚀**
