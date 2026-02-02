Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Получаем путь к текущей директории
ScriptPath = FSO.GetParentFolderName(WScript.ScriptFullName)

' Запускаем start_stable.bat в скрытом режиме
WshShell.Run """" & ScriptPath & "\start_stable.bat""", 0, False

' Ждем 3 секунды для запуска сервера
WScript.Sleep 3000

' Открываем браузер
WshShell.Run "http://127.0.0.1:8080", 1, False
