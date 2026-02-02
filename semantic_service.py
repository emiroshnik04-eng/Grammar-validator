import os
import json
from typing import Optional
import logging

import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настраиваем логирование
from logging_config import setup_logging
logger = setup_logging()


"""
Сервис для семантического анализа названий категорий через LLM.

Использует OpenAI API для умной проверки названий категорий каталога:
- Определяет нужно ли множественное число
- Учитывает контекст и иерархию категорий
- Понимает имена собственные и исключения

Настройка:
1. Создайте файл .env в корне проекта
2. Добавьте ваш API ключ: LLM_API_KEY=sk-your-key-here
3. (Опционально) Выберите модель: LLM_MODEL=gpt-4-turbo

Запуск:
    python -m uvicorn semantic_service:app --host 127.0.0.1 --port 8000 --reload

Документация API: http://127.0.0.1:8000/docs
"""


LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_API_URL = os.environ.get("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4-turbo")


app = FastAPI()


class CategoryRequest(BaseModel):
    name: str
    path: str


class CategoryResponse(BaseModel):
    should_be_plural: bool
    suggested_name: str
    reason: str


SYSTEM_PROMPT = """
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


async def ask_llm(name: str, path: str) -> Optional[CategoryResponse]:
    if not LLM_API_KEY:
        # если ключа нет — просто ничего не делаем
        return None

    prompt = (
        f"Путь категории в каталоге: {path}.\n"
        f"Текущее название уровня: {name!r}.\n"
        f"Реши, как оно должно выглядеть в финальном каталоге и нужно ли множественное число.\n"
        f"Верни JSON с полями should_be_plural, suggested_name, reason."
    )

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
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    return CategoryResponse(
        should_be_plural=bool(parsed.get("should_be_plural", False)),
        suggested_name=str(parsed.get("suggested_name", name)),
        reason=str(parsed.get("reason", "")),
    )


@app.post("/analyze-category", response_model=CategoryResponse)
async def analyze_category(req: CategoryRequest):
    result = await ask_llm(req.name, req.path)
    if result is None:
        # если LLM недоступен — вернуть "как есть"
        return CategoryResponse(
            should_be_plural=False,
            suggested_name=req.name,
            reason="LLM_API_KEY is not configured",
        )
    return result


class ErrorRequest(BaseModel):
    error_traceback: str


SYSTEM_PROMPT_ERROR = """
Ты опытный Python-разработчик. 
Твоя задача — проанализировать текст ошибки (traceback) и дать краткое, понятное объяснение причины и способ исправления.
Отвечай структурированно, в формате Markdown.
"""


@app.post("/analyze-error")
async def analyze_error(req: ErrorRequest):
    """
    Умный анализ ошибок через LLM API.
    Принимает traceback и возвращает понятное объяснение с решением.
    """
    if not LLM_API_KEY:
        logger.warning("Попытка анализа ошибки без настроенного API ключа")
        return {"explanation": "API ключ не настроен, я не могу проанализировать ошибку."}

    # Обрезаем traceback для логов
    traceback_preview = req.error_traceback[:200] + "..." if len(req.error_traceback) > 200 else req.error_traceback
    logger.info(f"Получен запрос на анализ ошибки: {traceback_preview}")

    prompt = f"Проанализируй эту ошибку:\n\n{req.error_traceback}"

    try:
        logger.debug(f"Отправка запроса к LLM API (модель: {LLM_MODEL})")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                LLM_API_URL,
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_ERROR},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
        resp.raise_for_status()
        data = resp.json()
        explanation = data["choices"][0]["message"]["content"]

        logger.info(f"Анализ ошибки выполнен успешно, длина ответа: {len(explanation)} символов")

        return {"explanation": explanation}
    except httpx.TimeoutException:
        logger.error("Таймаут при обращении к LLM API")
        return {"explanation": "Превышено время ожидания ответа от AI сервиса"}
    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка HTTP при обращении к LLM API: {e.response.status_code}")
        return {"explanation": f"Ошибка связи с AI сервисом: HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Неожиданная ошибка при анализе: {str(e)}", exc_info=True)
        return {"explanation": f"Не удалось связаться с AI для анализа ошибки: {e}"}




