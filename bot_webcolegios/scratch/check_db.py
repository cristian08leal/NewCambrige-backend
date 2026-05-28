
import psycopg2
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, GRADO_ID_DEFAULT

def check_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Check if table grados exists and has the default record
        cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'grados'")
        if cursor.fetchone()[0] == 0:
            print("Table 'grados' does not exist!")
            return
            
        cursor.execute(f"SELECT * FROM grados WHERE grado_id = {GRADO_ID_DEFAULT}")
        row = cursor.fetchone()
        if row:
            print(f"Default grade (id={GRADO_ID_DEFAULT}) exists: {row}")
        else:
            print(f"Default grade (id={GRADO_ID_DEFAULT}) is MISSING!")
            
        cursor.execute("SELECT count(*) FROM estudiantes")
        count = cursor.fetchone()[0]
        print(f"Number of students: {count}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
