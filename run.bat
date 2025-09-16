@echo off
setlocal

REM Активируем venv, если есть (опционально)
IF EXIST .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)

REM Проверка наличия файла .env и BOT_TOKEN
IF NOT EXIST ".env" (
  echo ❌ File .env not found. Create .env with BOT_TOKEN=... 
  exit /b 1
)

findstr /R /C:"^BOT_TOKEN=" .env >nul
IF ERRORLEVEL 1 (
  echo ❌ BOT_TOKEN not found in .env
  exit /b 1
)

set PYTHONUNBUFFERED=1
python main.py