@echo off
chcp 65001 >nul
setlocal

color 0B
echo.
echo ========================================
echo   Создание ярлыка на рабочем столе
echo ========================================
echo.

REM Получаем путь к рабочему столу
set DESKTOP=%USERPROFILE%\Desktop

REM Получаем путь к текущей директории
set CURRENT_DIR=%~dp0

REM Создаем VBS скрипт для создания ярлыка
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP%\Catalog Validator.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%CURRENT_DIR%start_stable.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Catalog Validator - Проверка каталогов товаров" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "shell32.dll,165" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

REM Запускаем VBS скрипт
cscript //nologo "%TEMP%\CreateShortcut.vbs"

REM Удаляем временный файл
del "%TEMP%\CreateShortcut.vbs"

if exist "%DESKTOP%\Catalog Validator.lnk" (
    color 0A
    echo [УСПЕХ] Ярлык создан на рабочем столе!
    echo.
    echo Теперь менеджеры могут запускать приложение
    echo просто дважды кликнув по ярлыку
    echo "Catalog Validator" на рабочем столе.
) else (
    color 0C
    echo [ОШИБКА] Не удалось создать ярлык!
)

echo.
echo ========================================
pause
