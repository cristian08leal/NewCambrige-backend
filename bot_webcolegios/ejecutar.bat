@echo off
title WebColegios Bot - Produccion
color 0B
echo.
echo  ==========================================
echo   INICIANDO SISTEMA WEBCOLEGIOS BOT...
echo  ==========================================
echo.

cd /d "%~dp0"

:: Verificar y activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo  [OK] Entorno virtual (venv) activado
) else if exist "..\venv_new\Scripts\activate.bat" (
    call ..\venv_new\Scripts\activate.bat
    echo  [OK] Entorno virtual (venv_new) activado
) else (
    echo  [WARNING] No se encontro entorno virtual. Usando Python del sistema.
)

:: Verificar archivo .env
if not exist ".env" (
    echo  [ERROR] No se encontro el archivo .env. Por favor, crea uno basado en .env.example.
    pause
    exit /b 1
)

echo.
echo  [OK] Inicializando base de datos...
python setup_db.py
if %errorlevel% neq 0 (
    echo  [ERROR] Fallo en la inicializacion de la base de datos.
    pause
    exit /b %errorlevel%
)

echo.
echo  [OK] Iniciando servidor web (Uvicorn)...
echo.
uvicorn app:app --host 0.0.0.0 --port 8000
pause
