import psycopg2
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM docentes;")
    total = cur.fetchone()[0]
    print(f"Total registros en tabla docentes: {total}")
    
    print("\nRegistros con sus cursos mapeados:")
    cur.execute("SELECT documento, nombre, grado_titular, curso_titular FROM docentes WHERE grado_titular IS NOT NULL LIMIT 15;")
    for row in cur.fetchall():
        print(f"Docente: {row[1]} -> Grado: {row[2]} -> Curso: {row[3]}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
