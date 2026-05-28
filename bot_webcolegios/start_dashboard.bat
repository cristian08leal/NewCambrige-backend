@echo off
title WebColegios Bot - Dashboard UI
color 0B
echo.
echo  ==========================================
echo   INICIANDO DASHBOARD WEBCOLEGIOS...
echo  ==========================================
echo.
cd /d "%~dp0"
call ..\venv_new\Scripts\activate.bat
echo  [OK] Entorno virtual activado
echo  [OK] Iniciando servidor web en http://localhost:8000
echo.
python app.py
pause
