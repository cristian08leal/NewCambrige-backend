# =============================================================================
# scratch/test_fase1.py — Script de validación automatizada para la Fase 1
# =============================================================================

import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import (
    obtener_estudiantes, obtener_docentes, verificar_duplicado,
    procesar_importacion_masiva, obtener_grupos
)

def run_tests():
    print("=" * 60)
    print("[INFO] INICIANDO VERIFICACION DE FASE 1")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # 1. Verificar importaciones del módulo fachada y consulta normalizada
    # -------------------------------------------------------------------------
    print("\n[1/4] Probando consulta normalizada de estudiantes...")
    estudiantes = obtener_estudiantes(limit=5)
    print(f"OK: Se obtuvieron {len(estudiantes)} estudiantes.")
    if estudiantes:
        sample = estudiantes[0]
        print(f"   Ejemplo de registro mapeado dinamicamente:")
        for k, v in sample.items():
            print(f"     - {k}: {repr(v)}")
        
        # Validar llaves requeridas por la UI
        required_keys = {"id", "documento", "nombre", "grado_texto", "curso", "titular", "jornada"}
        missing = required_keys - set(sample.keys())
        if missing:
            print(f"ERROR: Faltan llaves en el diccionario retornado: {missing}")
            sys.exit(1)
        else:
            print("   OK: Todas las llaves requeridas por el frontend estan presentes.")
    else:
        print("ADVERTENCIA: No hay estudiantes registrados para mostrar ejemplo.")

    print("\nProbando consulta normalizada de docentes...")
    docentes = obtener_docentes(limit=5)
    print(f"OK: Se obtuvieron {len(docentes)} docentes.")
    if docentes:
        sample_doc = docentes[0]
        print(f"   Ejemplo de docente mapeado:")
        for k, v in sample_doc.items():
            print(f"     - {k}: {repr(v)}")
    else:
        print("ADVERTENCIA: No hay docentes registrados para mostrar ejemplo.")

    # -------------------------------------------------------------------------
    # 2. Verificar duplicados
    # -------------------------------------------------------------------------
    print("\n[2/4] Probando verificacion de duplicados...")
    if estudiantes:
        doc_duplicado = estudiantes[0]["documento"]
        res_dup = verificar_duplicado("estudiante", None, doc_duplicado)
        if res_dup:
            print(f"   OK: Verificacion de duplicado exitosa. Encontrado: {res_dup['nombre']} ({res_dup['grado_texto']})")
        else:
            print("   ERROR: No se detecto duplicado existente.")
            sys.exit(1)

    # -------------------------------------------------------------------------
    # 3. Verificar importacion masiva tolerante a fallos (COD-03)
    # -------------------------------------------------------------------------
    print("\n[3/4] Probando importacion masiva tolerante a fallos (COD-03)...")
    lote_prueba = [
        # 1. Valido
        {
            "nombre": "Estudiante Prueba Uno",
            "documento": "TEST-999001",
            "codigo_interno": "TEST-999001",
            "grado": "Primero",
            "curso": "A",
            "jornada": "Completa"
        },
        # 2. Invalido (nombre vacio)
        {
            "nombre": "",
            "documento": "TEST-999002",
            "codigo_interno": "TEST-999002",
            "grado": "Primero",
            "curso": "A",
            "jornada": "Completa"
        },
        # 3. Invalido (grado no reconocido)
        {
            "nombre": "Estudiante Prueba Tres",
            "documento": "TEST-999003",
            "codigo_interno": "TEST-999003",
            "grado": "Grado Inexistente 99",
            "curso": "A",
            "jornada": "Completa"
        },
        # 4. Valido
        {
            "nombre": "Estudiante Prueba Cuatro",
            "documento": "TEST-999004",
            "codigo_interno": "TEST-999004",
            "grado": "Segundo",
            "curso": "A",
            "jornada": "Continua"
        }
    ]

    res_import = procesar_importacion_masiva("estudiante", lote_prueba)
    print(f"   Respuesta de la importacion:")
    print(f"     - Status: {res_import.get('status')}")
    print(f"     - Total OK: {res_import.get('total_ok')}")
    print(f"     - Total Rechazados: {res_import.get('total_rechazados')}")
    print(f"     - Mensaje: {res_import.get('message')}")
    
    print("   Detalles del log:")
    for log_item in res_import.get("log", []):
        print(f"     - Fila {log_item['fila']} ({log_item['nombre']}): {log_item['estado']} -> {log_item['razon']}")

    # Validaciones del test de tolerancia a fallos
    if res_import["total_ok"] != 2:
        print(f"ERROR: total_ok deberia ser 2, pero es {res_import['total_ok']}")
        sys.exit(1)
    if res_import["total_rechazados"] != 2:
        print(f"ERROR: total_rechazados deberia ser 2, pero es {res_import['total_rechazados']}")
        sys.exit(1)
        
    print("   OK: Tolerancia a fallos validada: los validos se insertaron y los invalidos se reportaron individualmente.")

    # Limpiar registros de prueba en la base de datos para no contaminar
    from modules.db_pool import get_connection, release_connection
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM estudiantes WHERE documento LIKE 'TEST-%';")
        conn.commit()
        print("   OK: Registros de prueba eliminados correctamente de la base de datos.")
    except Exception as cleanup_error:
        print(f"   ADVERTENCIA durante limpieza: {cleanup_error}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

    print("\n" + "=" * 60)
    print("RESUMEN: TODAS LAS PRUEBAS UNITARIAS DE FASE 1 PASARON EXITOSAMENTE!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
