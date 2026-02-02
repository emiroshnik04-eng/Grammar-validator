"""
Модуль для умного анализа ошибок через LLM API.
Автоматически отправляет traceback на анализ и получает рекомендации.
"""

import os
import traceback
import logging
from typing import Optional, Dict, Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# URL semantic service для анализа ошибок
SEMANTIC_URL = os.environ.get("SEMANTIC_URL", "http://127.0.0.1:8000")
ERROR_ANALYSIS_ENDPOINT = f"{SEMANTIC_URL}/analyze-error"
LLM_API_KEY = os.environ.get("LLM_API_KEY")


async def analyze_error_async(error: Exception, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Асинхронный анализ ошибки через LLM API.

    Args:
        error: Объект исключения
        context: Дополнительный контекст (имя файла, описание операции)

    Returns:
        Словарь с результатами анализа или None при неудаче
    """
    if not LLM_API_KEY:
        logger.debug("LLM API ключ не настроен, анализ ошибок недоступен")
        return None

    try:
        # Формируем traceback
        error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

        # Добавляем контекст если есть
        if context:
            error_traceback = f"Контекст: {context}\n\n{error_traceback}"

        logger.debug(f"Отправка ошибки на анализ: {type(error).__name__}")

        # Отправляем на анализ
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                ERROR_ANALYSIS_ENDPOINT,
                json={"error_traceback": error_traceback}
            )

            if response.status_code == 200:
                result = response.json()
                explanation = result.get("explanation", "")

                logger.info(f"Получен анализ ошибки: {explanation[:100]}...")

                return {
                    "success": True,
                    "explanation": explanation,
                    "error_type": type(error).__name__,
                    "error_message": str(error)
                }
            else:
                logger.warning(f"Ошибка при анализе: HTTP {response.status_code}")
                return None

    except httpx.TimeoutException:
        logger.warning("Таймаут при обращении к сервису анализа ошибок")
        return None
    except httpx.ConnectError:
        logger.debug("Сервис анализа ошибок недоступен")
        return None
    except Exception as e:
        logger.error(f"Не удалось проанализировать ошибку: {e}")
        return None


def analyze_error_sync(error: Exception, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Синхронная версия анализа ошибки (для использования вне async контекста).

    Args:
        error: Объект исключения
        context: Дополнительный контекст

    Returns:
        Словарь с результатами анализа или None при неудаче
    """
    if not LLM_API_KEY:
        return None

    try:
        error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

        if context:
            error_traceback = f"Контекст: {context}\n\n{error_traceback}"

        # Синхронный запрос
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                ERROR_ANALYSIS_ENDPOINT,
                json={"error_traceback": error_traceback}
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "explanation": result.get("explanation", ""),
                    "error_type": type(error).__name__,
                    "error_message": str(error)
                }
            return None

    except Exception as e:
        logger.debug(f"Не удалось проанализировать ошибку: {e}")
        return None


def format_error_response(analysis: Optional[Dict[str, Any]], original_error: str) -> str:
    """
    Форматирует ответ с анализом ошибки для пользователя.

    Args:
        analysis: Результат анализа от LLM
        original_error: Оригинальное сообщение об ошибке

    Returns:
        Отформатированное сообщение
    """
    if not analysis or not analysis.get("success"):
        return original_error

    explanation = analysis.get("explanation", "")

    return f"{original_error}\n\n💡 Умный анализ:\n{explanation}"


if __name__ == "__main__":
    # Тест анализа ошибок
    import asyncio

    async def test():
        try:
            # Намеренно вызываем ошибку
            result = 10 / 0
        except ZeroDivisionError as e:
            analysis = await analyze_error_async(e, context="Тестирование деления на ноль")
            if analysis:
                print("Анализ получен:")
                print(analysis["explanation"])
            else:
                print("Анализ недоступен (проверьте настройки LLM API)")

    asyncio.run(test())
