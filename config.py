"""
Конфигурация приложения Catalog Validator
"""
import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).parent

# Настройки сервера
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")  # 0.0.0.0 для доступа по сети
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))

# Режим работы
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")  # production или development

# Настройки безопасности
# Если нужна авторизация - раскомментируйте и установите
# REQUIRE_AUTH = True
# AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
# AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "changeme")

# Настройки загрузки файлов
MAX_FILE_SIZE_MB = 50  # Максимальный размер файла в МБ
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"

# Создание необходимых директорий
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "catalog_validator.log"

# Настройки OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Проверка конфигурации
def check_config():
    """Проверка корректности конфигурации"""
    issues = []

    if not OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY не установлен! Установите переменную окружения.")

    if SERVER_HOST == "0.0.0.0" and ENVIRONMENT == "production":
        print(f"[INFO] Сервер доступен по сети на порту {SERVER_PORT}")

    if issues:
        print("[ВНИМАНИЕ] Проблемы конфигурации:")
        for issue in issues:
            print(f"  - {issue}")

    return len(issues) == 0

if __name__ == "__main__":
    print("=" * 60)
    print("Конфигурация Catalog Validator")
    print("=" * 60)
    print(f"Хост: {SERVER_HOST}")
    print(f"Порт: {SERVER_PORT}")
    print(f"Окружение: {ENVIRONMENT}")
    print(f"OpenAI API Key: {'Установлен' if OPENAI_API_KEY else 'НЕ УСТАНОВЛЕН'}")
    print("=" * 60)
    check_config()
