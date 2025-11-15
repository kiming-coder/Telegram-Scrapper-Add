@echo off
chcp 65001 >nul
echo 🔧 Installing Python Dependencies...
echo.
pip install -r requirements.txt
echo.
echo ✅ Installation Complete!
echo.
pause
