@echo off
chcp 65001 >nul
echo ============================================================
echo 🤖 Настройка Semantic Service для Catalog Validator
echo ============================================================
echo.

REM Проверка наличия .env файла
if not exist .env (
    echo ❌ Файл .env не найден!
    echo.
    echo 📝 Инструкция:
    echo 1. Скопируйте файл .env.example в .env
    echo 2. Откройте .env и вставьте ваш OpenAI API ключ
    echo 3. Запустите этот скрипт снова
    echo.
    pause
    exit /b 1
)

echo ✅ Файл .env найден
echo.

REM Загрузка переменных из .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%b"=="" (
        REM Пропускаем комментарии
        echo %%a | findstr /b "#" >nul
        if errorlevel 1 (
            set "%%a=%%b"
            echo Загружена переменная: %%a
        )
    )
)

echo.
echo ============================================================
echo 📋 Текущие настройки:
echo ============================================================
echo LLM_API_URL: %LLM_API_URL%
echo LLM_MODEL: %LLM_MODEL%
echo SEMANTIC_URL: %SEMANTIC_URL%
echo LLM_API_KEY: %LLM_API_KEY:~0,8%******
echo ============================================================
echo.

echo 🚀 Запуск semantic_service...
echo.
echo 📍 Сервис будет доступен по адресу: http://127.0.0.1:8000
echo 📝 Для остановки нажмите: Ctrl+C
echo.
echo ============================================================

python -m uvicorn semantic_service:app --host 127.0.0.1 --port 8000 --reload

pause
