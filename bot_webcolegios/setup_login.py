#!/usr/bin/env python3
# =============================================================================
# setup_login.py — Script de configuración inicial de credenciales (SEG-03/04)
# =============================================================================
# Ejecutar UNA VEZ después de apply migrate_criticos_fase0.sql:
#   python setup_login.py
#
# Lee la credencial de WebColegios desde variables de entorno o las pide
# interactivamente, las cifra con Fernet y las guarda en la tabla login.
# =============================================================================

import os
import sys
import psycopg2
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

# ── Parámetros BD ─────────────────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_NAME     = os.getenv("DB_NAME", "paz_y_salvo")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

if not DB_PASSWORD:
    print("[ERROR] DB_PASSWORD no está definida en el .env")
    sys.exit(1)

if not ENCRYPTION_KEY:
    print("[ERROR] ENCRYPTION_KEY no está definida en el .env")
    print("  Genera una con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    sys.exit(1)


def run_migration(conn):
    """Ejecuta el SQL de migración de la Fase 0."""
    sql_file = os.path.join(os.path.dirname(__file__), "sql", "migrate_criticos_fase0.sql")
    if not os.path.exists(sql_file):
        print(f"[WARN] No se encontró {sql_file} — omitiendo migración.")
        return
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    print("[OK] Migración aplicada correctamente.")


def registrar_credencial(conn, url, usuario, password, tipo_usuario):
    """Cifra la contraseña y la inserta en la tabla login."""
    fernet = Fernet(ENCRYPTION_KEY.encode())
    password_enc = fernet.encrypt(password.encode()).decode()

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO login (url_plataforma, usuario, password_enc, tipo_usuario, activo)
        VALUES (%s, %s, %s, %s, TRUE)
        RETURNING id;
    """, (url, usuario, password_enc, tipo_usuario))
    login_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return login_id


def main():
    print("=" * 60)
    print("  Setup de credenciales WebColegios (Fase 0 - SEG-03)")
    print("=" * 60)

    # Conectar a la BD
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD, connect_timeout=10
        )
        print(f"[OK] Conectado a PostgreSQL: {DB_NAME}@{DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        sys.exit(1)

    # Ejecutar migración
    try:
        run_migration(conn)
    except Exception as e:
        print(f"[ERROR] Error en migración: {e}")
        conn.close()
        sys.exit(1)

    # Verificar si ya hay credenciales registradas
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM login WHERE activo = TRUE;")
    existing = cursor.fetchone()[0]
    cursor.close()

    if existing > 0:
        print(f"[INFO] Ya existen {existing} credencial(es) activa(s) en la tabla login.")
        resp = input("  ¿Deseas agregar otra credencial? (s/N): ").strip().lower()
        if resp != "s":
            print("[OK] Configuración completada. No se agregaron nuevas credenciales.")
            conn.close()
            return

    # Leer credenciales desde .env o pedir interactivamente
    web_url      = os.getenv("WEB_URL", "").strip()
    web_usuario  = os.getenv("WEB_USUARIO", "").strip()
    web_password = os.getenv("WEB_PASSWORD", "").strip()
    web_tipo     = os.getenv("WEB_TIPO_USUARIO", "Administrativo").strip()

    print("\n  Credenciales de la plataforma WebColegios:")

    if web_url:
        print(f"  URL          : {web_url} (desde .env)")
    else:
        web_url = input("  URL          : ").strip()

    if web_usuario:
        print(f"  Usuario      : {web_usuario} (desde .env)")
    else:
        web_usuario = input("  Usuario      : ").strip()

    if web_password:
        print("  Contraseña   : ******** (desde .env)")
    else:
        import getpass
        web_password = getpass.getpass("  Contraseña   : ")

    if not web_url or not web_usuario or not web_password:
        print("[ERROR] URL, usuario y contraseña son obligatorios.")
        conn.close()
        sys.exit(1)

    # Guardar en la BD
    try:
        login_id = registrar_credencial(conn, web_url, web_usuario, web_password, web_tipo)
        print(f"\n[OK] Credencial registrada con ID={login_id}")
        print("     La contraseña ha sido cifrada con Fernet (ENCRYPTION_KEY del .env).")
        print("\n[IMPORTANTE] Ahora puedes eliminar WEB_USUARIO y WEB_PASSWORD del .env")
        print("             ya que el sistema los cargará desde la tabla login.")
    except Exception as e:
        print(f"[ERROR] Error registrando credencial: {e}")
        conn.close()
        sys.exit(1)

    conn.close()
    print("\nSetup completado exitosamente.")
    print("=" * 60)


if __name__ == "__main__":
    main()
