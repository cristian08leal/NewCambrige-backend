import os
import sys
import psycopg2
from dotenv import load_dotenv

# Asegurar que estamos en el directorio correcto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

def setup_database():
    print(f"🔄 Conectando a la base de datos {DB_NAME} en {DB_HOST}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        sql_file = os.path.join(os.path.dirname(__file__), 'sql', 'setup.sql')
        if not os.path.exists(sql_file):
            print(f"❌ Error: No se encontró el archivo {sql_file}")
            sys.exit(1)
            
        print(f"📂 Leyendo DDL desde {sql_file}...")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        print("⚡ Ejecutando migraciones e inicializando catálogos...")
        cursor.execute(sql_script)
        
        # Nuevas migraciones Sprint 2 y Tablas de Staging
        migraciones = [
            'migrate_sprint2_indices.sql',
            'migrate_sprint2_auditoria.sql',
            'migrate_staging_tables.sql'
        ]
        
        for mig_file in migraciones:
            mig_path = os.path.join(os.path.dirname(__file__), 'sql', mig_file)
            if os.path.exists(mig_path):
                print(f"📂 Aplicando migración: {mig_file}...")
                with open(mig_path, 'r', encoding='utf-8') as f:
                    cursor.execute(f.read())
            
        conn.commit()
        print("✅ Base de datos inicializada correctamente.")
        
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        print(f"❌ Error durante la inicialización de la base de datos: {e}")
        sys.exit(1)
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    load_dotenv()
    setup_database()
