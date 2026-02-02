#!/bin/bash

# ============================================
# Скрипт установки Catalog Validator на Linux
# ============================================

set -e

echo "========================================"
echo "  Установка Catalog Validator"
echo "========================================"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "[ОШИБКА] Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Проверка наличия Python 3.8+
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] Python 3 не установлен!"
    echo "Установите: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

# Создание директории
INSTALL_DIR="/opt/catalog-validator"
echo "[1/8] Создание директории $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Копирование файлов (если запускаем из директории проекта)
if [ -f "../web_app.py" ]; then
    echo "[2/8] Копирование файлов проекта..."
    cp ../*.py ./ 2>/dev/null || true
    cp ../requirements.txt ./ 2>/dev/null || true
    cp ../.env.example ./.env 2>/dev/null || true
fi

# Создание виртуального окружения
echo "[3/8] Создание виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
echo "[4/8] Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
if [ -f "requirements.txt" ]; then
    echo "[5/8] Установка зависимостей..."
    pip install -r requirements.txt
else
    echo "[ВНИМАНИЕ] requirements.txt не найден!"
    echo "Установка базовых зависимостей..."
    pip install fastapi uvicorn pandas openpyxl python-dotenv httpx slowapi openai pymorphy3
fi

# Создание директорий для логов
echo "[6/8] Создание директорий для логов..."
mkdir -p /var/log/catalog-validator
chown www-data:www-data /var/log/catalog-validator

# Создание директорий для загрузок
mkdir -p uploads outputs
chown -R www-data:www-data "$INSTALL_DIR"

# Копирование systemd service
echo "[7/8] Установка systemd service..."
if [ -f "catalog-validator.service" ]; then
    cp catalog-validator.service /etc/systemd/system/

    # Запрос API ключа OpenAI
    echo ""
    echo "========================================"
    read -p "Введите ваш OpenAI API ключ: " OPENAI_KEY
    echo "========================================"

    # Обновление API ключа в service файле
    sed -i "s/your_api_key_here/$OPENAI_KEY/" /etc/systemd/system/catalog-validator.service

    # Перезагрузка systemd
    systemctl daemon-reload

    echo ""
    echo "[8/8] Включение автозапуска..."
    systemctl enable catalog-validator

    echo ""
    echo "========================================"
    echo "  Установка завершена!"
    echo "========================================"
    echo ""
    echo "Для управления сервисом используйте:"
    echo "  sudo systemctl start catalog-validator    # Запустить"
    echo "  sudo systemctl stop catalog-validator     # Остановить"
    echo "  sudo systemctl status catalog-validator   # Статус"
    echo "  sudo systemctl restart catalog-validator  # Перезапустить"
    echo ""
    echo "Логи:"
    echo "  sudo journalctl -u catalog-validator -f"
    echo ""

    read -p "Запустить сервис сейчас? (y/n): " START_NOW
    if [ "$START_NOW" = "y" ] || [ "$START_NOW" = "Y" ]; then
        systemctl start catalog-validator

        # Получение IP адреса
        IP_ADDR=$(hostname -I | awk '{print $1}')

        echo ""
        echo "========================================"
        echo "  Сервис запущен!"
        echo "========================================"
        echo ""
        echo "Доступ для менеджеров:"
        echo "  http://$IP_ADDR:8080"
        echo ""
        echo "========================================"
    fi
else
    echo "[ВНИМАНИЕ] catalog-validator.service не найден!"
    echo "Запускайте вручную через: python3 web_app.py"
fi

echo ""
echo "Готово!"
