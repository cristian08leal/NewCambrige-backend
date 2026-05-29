import psycopg2

conn = psycopg2.connect(
    host='localhost',
    user='postgres',
    password='Cristianlecr.2025',
    dbname='postgres'
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_database WHERE datname='newcambridge'")
exists = cur.fetchone()

if exists:
    print("✅ La base de datos 'newcambridge' ya existe.")
else:
    cur.execute("CREATE DATABASE newcambridge")
    print("✅ Base de datos 'newcambridge' creada exitosamente.")

conn.close()
