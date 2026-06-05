@echo off
setlocal

cd /d "%~dp0"

py -3 -m venv .build-venv
call .build-venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m PyInstaller --clean --noconfirm aurora.spec

echo.
echo Build Windows criado em: dist\aurora-chat.exe
echo Execute com: dist\aurora-chat.exe

endlocal
