@echo off
chcp 65001 >nul
setlocal

REM Переход в директорию скрипта
cd /d "%~dp0"

color 0B
echo.
echo ========================================
echo   CATALOG VALIDATOR - Запуск сервера
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

REM Проверка файла
if not exist "web_app.py" (
    color 0C
    echo [ОШИБКА] web_app.py не найден!
    echo.
    pause
    exit /b 1
)

echo [OK] Запуск сервера...
echo.
echo Сервер будет доступен по адресу:
echo     http://127.0.0.1:8080
echo.
echo [i] Браузер откроется автоматически через 3 секунды
echo [i] Для остановки нажмите Ctrl+C
echo ========================================
echo.

REM Запуск сервера в фоне
start /B python web_app.py

REM Ожидание запуска (3 секунды)
ping 127.0.0.1 -n 4 >nul

REM Открытие браузера
start http://127.0.0.1:8080

echo [OK] Браузер открыт!
echo [i] Не закрывайте это окно пока работаете с приложением
echo.

REM Ожидание завершения
pause
