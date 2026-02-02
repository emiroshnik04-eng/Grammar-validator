"""
Конфигурация логирования для Catalog Validator.
Настраивает логирование в файл и консоль с ротацией.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = "catalog_validator.log") -> logging.Logger:
    """
    Настройка логирования для приложения.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов

    Returns:
        Настроенный logger
    """
    # Формат логов
    log_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Получаем корневой logger
    root_logger = logging.getLogger()

    # Очищаем существующие handlers, если есть
    root_logger.handlers.clear()

    # Устанавливаем уровень
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Консольный handler (выводит INFO и выше)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Файловый handler с ротацией (выводит DEBUG и выше)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 МБ
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        root_logger.warning(f"Не удалось создать файл логов {log_file}: {e}")

    # Создаем логгер для нашего приложения
    app_logger = logging.getLogger("catalog_validator")

    return app_logger


# Создаем глобальный logger для использования в других модулях
logger = setup_logging()


if __name__ == "__main__":
    # Тестирование логирования
    logger.debug("Это DEBUG сообщение")
    logger.info("Это INFO сообщение")
    logger.warning("Это WARNING сообщение")
    logger.error("Это ERROR сообщение")
    logger.critical("Это CRITICAL сообщение")

    print("\nЛоги записаны в catalog_validator.log")
