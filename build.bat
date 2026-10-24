@echo off
setlocal
cd /d "%~dp0"
python make_icon.py
if errorlevel 1 exit /b 1
if /I "%~1"=="fast" goto fast
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Clawd --icon clawd.ico main.py
if errorlevel 1 exit /b 1
if exist dist\config.json del /Q dist\config.json
echo Built dist\Clawd.exe
goto :eof

:fast
python -m PyInstaller --noconfirm --onedir --windowed --name Clawd --icon clawd.ico --log-level WARN main.py
if errorlevel 1 exit /b 1
if exist dist\Clawd\config.json del /Q dist\Clawd\config.json
echo Built dist\Clawd\Clawd.exe
