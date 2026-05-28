# =============================================================================
# scratch/test_api_urllib.py — Script de prueba de API y Seguridad (urllib)
# =============================================================================

import sys
import os
import subprocess
import time
import urllib.request
import urllib.error
import json

# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import API_KEY

def run_tests():
    print("=" * 60)
    print("[INFO] INICIANDO PRUEBAS DE API Y SEGURIDAD (CON SERVER REAL)")
    print("=" * 60)

    # Iniciar servidor Uvicorn en el puerto de prueba 8090
    print("[1/4] Levantando servidor Uvicorn de prueba en puerto 8090...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8090"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3) # Esperar que inicie el servidor

    try:
        # 1. Probar GET /api/health
        print("\n[2/4] Probando endpoint de salud /api/health...")
        req = urllib.request.Request("http://127.0.0.1:8090/api/health")
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            print(f"   Status Code: 200")
            print(f"   Response: {res}")
            assert res["status"] == "ok"
            assert res["database"] == "healthy"
            print("   OK: Endpoint de salud validado correctamente.")

        # 2. Probar Seguridad (sin API Key)
        print("\n[3/4] Probando proteccion sin API Key en POST /api/import/manual...")
        datos_manual = {
            "tipo": "estudiante",
            "nombre": "Prueba API Sin Key",
            "documento_nacional": "1234567890",
            "grado": "Primero",
            "curso": "A",
            "jornada": "Completa"
        }
        
        req_blocked = urllib.request.Request(
            "http://127.0.0.1:8090/api/import/manual",
            data=json.dumps(datos_manual).encode(),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            urllib.request.urlopen(req_blocked)
            print("   ERROR: Se permitio el acceso sin API Key.")
            sys.exit(1)
        except urllib.error.HTTPError as e:
            print(f"   Status Code: {e.code}")
            print(f"   Response: {e.read().decode()}")
            assert e.code == 401
            print("   OK: Bloqueo sin API Key verificado correctamente (HTTP 401).")

        # 3. Probar Seguridad (con API Key correcta)
        print("\n[4/4] Probando autorizacion con API Key correcta en POST /api/import/manual...")
        req_allowed = urllib.request.Request(
            "http://127.0.0.1:8090/api/import/manual",
            data=json.dumps(datos_manual).encode(),
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            }
        )
        
        with urllib.request.urlopen(req_allowed) as response:
            res = json.loads(response.read().decode())
            print(f"   Status Code: 200")
            print(f"   Response: {res}")
            assert res["status"] == "ok"
            print("   OK: Autorizacion con API Key exitosa.")

    finally:
        print("\n[CLEANUP] Finalizando servidor de prueba...")
        proc.terminate()
        proc.wait()
        print("[CLEANUP] Servidor finalizado.")

    # Limpiar registro creado de prueba
    from modules.db_pool import get_connection, release_connection
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM estudiantes WHERE documento = '1234567890';")
        conn.commit()
        print("[CLEANUP] Limpieza de base de datos completada.")
    except Exception as cleanup_error:
        print(f"⚠️ Advertencia durante limpieza: {cleanup_error}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

    print("\n" + "=" * 60)
    print("RESUMEN: TODAS LAS PRUEBAS DE API Y SEGURIDAD PASARON EXITOSAMENTE!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
