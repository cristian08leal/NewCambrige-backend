import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import get_connection, asegurar_tablas_docentes

conn = get_connection()
cur = conn.cursor()
asegurar_tablas_docentes(cur)
conn.commit()

# Verificar que el trigger existe
cur.execute("""
    SELECT trigger_name, event_manipulation, action_timing
    FROM information_schema.triggers
    WHERE trigger_name = 'trg_sync_titular_estudiantes';
""")
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"[OK] Trigger '{r[0]}' | evento: {r[1]} | timing: {r[2]}")
else:
    print("[ERROR] Trigger no encontrado")

# Verificar la funcion
cur.execute("""
    SELECT routine_name FROM information_schema.routines
    WHERE routine_name = 'fn_sync_titular_estudiantes';
""")
fn = cur.fetchone()
print(f"[OK] Funcion '{fn[0]}' registrada" if fn else "[ERROR] Funcion no encontrada")

conn.close()
