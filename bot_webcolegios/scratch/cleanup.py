import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import get_connection

def cleanup():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM estudiantes WHERE documento IN (SELECT documento FROM docentes);")
    deleted = cur.rowcount
    conn.commit()
    print(f"Limpiados {deleted} registros de maestros de la tabla estudiantes.")
    conn.close()

if __name__ == "__main__":
    cleanup()
