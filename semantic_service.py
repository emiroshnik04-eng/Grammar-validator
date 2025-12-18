import os
import json
from typing import Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel


"""
Небольшой сервис‑«мозг» для анализа названий категорий каталога.

- запрашивается из `check_catalog.py` по HTTP;
- внутри ходит в LLM‑API (OpenAI‑совместимый endpoint) и просит
  филологическую рекомендацию: нужно ли множественное число и как
  должна выглядеть категория.

ВАЖНО: ключ API не хранится в коде, а берётся из переменной среды
`LLM_API_KEY`. Перед запуском сервиса в PowerShell выполни:

    setx LLM_API_KEY "ТВОЙ_КЛЮЧ"

после этого открой новое окно PowerShell.
"""


LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_API_URL = os.environ.get("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")


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
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
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




