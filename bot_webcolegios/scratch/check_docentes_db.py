import psycopg2
from config.settings import DB_URL

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT documento, nombre, grado_titular FROM docentes WHERE grado_titular IS NOT NULL;")
    rows = cur.fetchall()
    print(f"Total titulares en DB: {len(rows)}")
    for r in rows[:5]:
        print(f"Docente: {r[1]} -> Grado: {r[2]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
