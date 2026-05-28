#!/bin/bash
echo "=========================================="
echo " INICIANDO SISTEMA WEBCOLEGIOS BOT... "
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Verificar y activar entorno virtual
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "[OK] Entorno virtual (venv) activado"
elif [ -f "../venv_new/bin/activate" ]; then
    source ../venv_new/bin/activate
    echo "[OK] Entorno virtual (venv_new) activado"
else
    echo "[WARNING] No se encontró entorno virtual. Usando Python del sistema."
fi

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "[ERROR] No se encontró el archivo .env. Por favor, crea uno basado en .env.example."
    exit 1
fi

echo ""
echo "[OK] Inicializando base de datos..."
python setup_db.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Fallo en la inicialización de la base de datos."
    exit 1
fi

echo ""
echo "[OK] Iniciando servidor web (Uvicorn)..."
echo ""
uvicorn app:app --host 0.0.0.0 --port 8000
