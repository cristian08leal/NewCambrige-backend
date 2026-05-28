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
    cur.execute("DELETE FROM docentes;")
    conn.commit()
    print("Tabla docentes limpiada correctamente.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
