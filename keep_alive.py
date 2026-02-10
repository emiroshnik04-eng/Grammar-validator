"""
Keep-alive скрипт для предотвращения засыпания Render.com сервиса
Пингует сервис каждые 10 минут
"""
import time
import requests
from datetime import datetime

SERVICE_URL = "https://catalog-validator.onrender.com/api/health"
PING_INTERVAL = 600  # 10 минут в секундах

def ping_service():
    """Отправляет ping запрос к сервису"""
    try:
        response = requests.get(SERVICE_URL, timeout=10)
        if response.status_code == 200:
            print(f"✓ [{datetime.now().strftime('%H:%M:%S')}] Сервис активен")
            return True
        else:
            print(f"✗ [{datetime.now().strftime('%H:%M:%S')}] Ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ [{datetime.now().strftime('%H:%M:%S')}] Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Keep-Alive скрипт для Grammar Validator")
    print(f"URL: {SERVICE_URL}")
    print(f"Интервал пинга: {PING_INTERVAL // 60} минут")
    print("=" * 60)
    print("\nНажмите Ctrl+C для остановки\n")

    while True:
        ping_service()
        time.sleep(PING_INTERVAL)
