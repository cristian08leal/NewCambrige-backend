import psycopg2
import sys
sys.path.insert(0, '.')
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='estudiantes' ORDER BY ordinal_position;")
print("COLUMNAS estudiantes:")
for r in cur.fetchall():
    print(" ", r)

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='docentes' ORDER BY ordinal_position;")
print("COLUMNAS docentes:")
for r in cur.fetchall():
    print(" ", r)

cur.execute("SELECT COUNT(*) FROM estudiantes;")
print("COUNT estudiantes:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM docentes;")
print("COUNT docentes:", cur.fetchone()[0])

# Mostrar primeros 3 docentes como muestra
cur.execute("SELECT * FROM docentes LIMIT 3;")
print("MUESTRA docentes:", cur.fetchall())

cur.close()
conn.close()
print("OK")
