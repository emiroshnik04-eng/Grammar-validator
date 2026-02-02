@echo off
chcp 65001 >nul
setlocal

REM ============================================
REM  CATALOG VALIDATOR - СЕРВЕРНЫЙ ЗАПУСК
REM ============================================

cd /d "%~dp0"

color 0B
echo.
echo ========================================
echo   CATALOG VALIDATOR - Серверный режим
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ОШИБКА] Python не найден!
    echo Установите Python с https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Проверка web_app.py
if not exist "web_app.py" (
    color 0C
    echo [ОШИБКА] web_app.py не найден!
    echo.
    pause
    exit /b 1
)

REM Установка переменных окружения для сервера
set SERVER_HOST=0.0.0.0
set SERVER_PORT=8080
set ENVIRONMENT=production

echo [OK] Запуск сервера в сетевом режиме...
echo.
echo ========================================
echo   НАСТРОЙКИ СЕРВЕРА
echo ========================================
echo  Хост: %SERVER_HOST% (доступен по сети)
echo  Порт: %SERVER_PORT%
echo  Окружение: %ENVIRONMENT%
echo ========================================
echo.
echo [i] Менеджеры смогут подключиться по адресу:
echo     http://^<IP_СЕРВЕРА^>:%SERVER_PORT%
echo.
echo [i] Чтобы узнать IP сервера, откройте новое окно
echo     командной строки и выполните: ipconfig
echo     (ищите IPv4 Address)
echo.
echo [i] Для остановки нажмите Ctrl+C
echo ========================================
echo.

REM Запуск сервера
python web_app.py

pause
