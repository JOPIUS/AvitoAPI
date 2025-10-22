@echo off
echo Убиваем старый процесс...
taskkill /f /im python.exe 2>nul

echo Ждем 2 секунды...
timeout /t 2 /nobreak >nul

echo Запускаем сервер в новом окне...
start "Avito Messenger Server" cmd /k python messenger_app.py

echo Ждем 8 секунд для запуска сервера...
timeout /t 8 /nobreak

echo Тестируем endpoint метрик...
python test_metrics_endpoint.py

pause
