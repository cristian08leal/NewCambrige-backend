# =============================================================================
# scratch/test_api.py — Script de prueba de API y Seguridad (FastAPI TestClient)
# =============================================================================

import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app import app
from config.settings import API_KEY

client = TestClient(app)

def run_api_tests():
    print("=" * 60)
    print("[INFO] INICIANDO PRUEBAS DE API Y SEGURIDAD")
    print("=" * 60)

    # 1. Probar GET /api/health
    print("\n[1/3] Probando endpoint de salud /api/health...")
    response = client.get("/api/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "healthy"
    print("✅ Endpoint de salud verificado correctamente.")

    # 2. Probar Seguridad (sin API Key)
    print("\n[2/3] Probando protección sin API Key en POST /api/import/manual...")
    datos_manual = {
        "tipo": "estudiante",
        "nombre": "Prueba API Sin Key",
        "documento_nacional": "1234567890",
        "grado": "Primero",
        "curso": "A",
        "jornada": "Completa"
    }
    response_no_key = client.post("/api/import/manual", json=datos_manual)
    print(f"Status Code sin Key: {response_no_key.status_code}")
    print(f"Response sin Key: {response_no_key.json()}")
    assert response_no_key.status_code == 401
    assert "API Key" in response_no_key.json()["detail"]
    print("✅ Bloqueo sin API Key verificado correctamente (HTTP 401).")

    # 3. Probar Seguridad (con API Key correcta)
    print("\n[3/3] Probando autorización con API Key correcta en POST /api/import/manual...")
    headers = {"X-API-Key": API_KEY}
    response_with_key = client.post("/api/import/manual", json=datos_manual, headers=headers)
    print(f"Status Code con Key: {response_with_key.status_code}")
    print(f"Response con Key: {response_with_key.json()}")
    assert response_with_key.status_code == 200
    assert response_with_key.json()["status"] == "ok"
    print("✅ Autorización con API Key y procesamiento manual exitoso.")

    # Limpiar registro creado de prueba
    from modules.db_pool import get_connection, release_connection
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM estudiantes WHERE documento = '1234567890';")
        conn.commit()
        print("\n🧹 Limpieza de registro de prueba completada.")
    except Exception as cleanup_error:
        print(f"⚠️ Advertencia durante limpieza: {cleanup_error}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

    print("\n" + "=" * 60)
    print("🎉 TODAS LAS PRUEBAS DE API Y SEGURIDAD PASARON EXITOSAMENTE!")
    print("=" * 60)

if __name__ == "__main__":
    run_api_tests()
