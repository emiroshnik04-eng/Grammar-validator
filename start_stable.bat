@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Получение текущей директории
cd /d "%~dp0"

REM Настройка цветов для консоли
color 0A

echo.
echo ========================================
echo   CATALOG VALIDATOR - СТАБИЛЬНЫЙ ЗАПУСК
echo ========================================
echo.
echo [i] Этот скрипт будет автоматически
echo     перезапускать сервер при сбоях
echo.
echo [i] Для полной остановки закройте это окно
echo ========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ОШИБКА] Python не найден!
    echo.
    echo Пожалуйста, установите Python с https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Проверка наличия зависимостей
if not exist "requirements.txt" (
    color 0E
    echo [ВНИМАНИЕ] Файл requirements.txt не найден!
    echo.
)

REM Проверка наличия главного файла
if not exist "web_app.py" (
    color 0C
    echo [ОШИБКА] Файл web_app.py не найден!
    echo.
    echo Убедитесь, что вы находитесь в правильной директории.
    echo.
    pause
    exit /b 1
)

REM Счетчик перезапусков
set RESTART_COUNT=0
set MAX_RESTARTS=10

:RESTART_LOOP

REM Проверка лимита перезапусков
if !RESTART_COUNT! GEQ %MAX_RESTARTS% (
    color 0C
    echo.
    echo ========================================
    echo [КРИТИЧЕСКАЯ ОШИБКА]
    echo Сервер перезапускался %MAX_RESTARTS% раз подряд!
    echo Возможно, есть серьезная проблема.
    echo ========================================
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

REM Увеличение счетчика
set /a RESTART_COUNT+=1

echo.
echo ========================================
echo [%date% %time%] Запуск #!RESTART_COUNT!
echo ========================================
echo.
echo [OK] Сервер будет доступен по адресу:
echo      http://127.0.0.1:8080
echo.

REM Запуск сервера
python web_app.py

REM Проверка кода выхода
set EXIT_CODE=%errorlevel%

echo.
echo ========================================
echo [%date% %time%] Сервер остановлен
echo Код выхода: %EXIT_CODE%
echo ========================================
echo.

REM Если выход был нормальным (Ctrl+C), не перезапускаем
if %EXIT_CODE% EQU 0 (
    echo [i] Сервер остановлен пользователем
    echo.
    pause
    exit /b 0
)

REM Сервер упал - перезапускаем через 3 секунды
color 0E
echo [ВНИМАНИЕ] Обнаружен сбой! Перезапуск через 3 секунды...
echo [i] Для отмены закройте это окно
echo.

REM Ожидание 3 секунды
ping 127.0.0.1 -n 4 >nul

REM Сброс счетчика если прошло больше 60 секунд
REM (это означает, что сервер работал какое-то время)
set RESTART_COUNT=0

goto RESTART_LOOP
