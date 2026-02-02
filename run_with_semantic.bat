@echo off
chcp 65001 >nul
echo ============================================================
echo 🔍 Catalog Validator с Semantic Service
echo ============================================================
echo.

REM Проверка наличия .env файла
if not exist .env (
    echo ❌ Файл .env не найден!
    echo.
    echo 📝 Сначала создайте файл .env с вашим API ключом
    echo    Смотрите .env.example для примера
    echo.
    pause
    exit /b 1
)

echo ✅ Загрузка настроек из .env...
echo.

REM Загрузка переменных из .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%b"=="" (
        echo %%a | findstr /b "#" >nul
        if errorlevel 1 (
            set "%%a=%%b"
        )
    )
)

echo ✅ Настройки загружены
echo 🤖 Semantic Service URL: %SEMANTIC_URL%
echo.

REM Проверка что semantic_service запущен
echo 🔍 Проверка доступности semantic_service...
curl -s http://127.0.0.1:8000/docs >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  ВНИМАНИЕ: Semantic service не запущен!
    echo.
    echo 📝 Откройте новое окно терминала и запустите:
    echo    setup_semantic.bat
    echo.
    echo Или нажмите Enter чтобы продолжить без semantic service...
    pause
) else (
    echo ✅ Semantic service работает
    echo.
)

echo ============================================================
echo 🚀 Запуск проверки каталога...
echo ============================================================
echo.

python check_catalog.py

echo.
echo ============================================================
echo ✅ Готово!
echo ============================================================
pause
