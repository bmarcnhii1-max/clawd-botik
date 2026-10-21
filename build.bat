@echo off
setlocal
cd /d "%~dp0"
python make_icon.py
if errorlevel 1 exit /b 1
if /I "%~1"=="fast" goto fast
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Clawd --icon clawd.ico main.py
if errorlevel 1 exit /b 1
if exist config.json copy /Y config.json dist\config.json >nul
echo Built dist\Clawd.exe
goto :eof

:fast
python -m PyInstaller --noconfirm --onedir --windowed --name Clawd --icon clawd.ico --log-level WARN main.py
if errorlevel 1 exit /b 1
if exist config.json copy /Y config.json dist\Clawd\config.json >nul
echo Built dist\Clawd\Clawd.exe
