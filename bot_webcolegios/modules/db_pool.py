# =============================================================================
# modules/db_pool.py — Pool de conexiones y credenciales cifradas (BD-01, SEG-03)
# =============================================================================

import psycopg2
from psycopg2 import Error, pool
from psycopg2.extensions import connection as PgConnection
from cryptography.fernet import Fernet
from typing import Dict, Optional
from utils.logger import get_logger
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, ENCRYPTION_KEY

logger = get_logger("db_pool")

_db_pool: Optional[pool.ThreadedConnectionPool] = None


def _init_pool() -> None:
    """
    Inicializa el pool de conexiones de forma lazy.
    minconn=2, maxconn=10 como indica el requerimiento BD-01.
    """
    global _db_pool
    if _db_pool is None or _db_pool.closed:
        try:
            _db_pool = pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=10,
            )
            logger.info("✅ Pool de conexiones PostgreSQL inicializado (min=2, max=10)")
        except Error as e:
            logger.error(f"❌ Error al inicializar pool de conexiones: {e}")
            raise


def get_connection() -> PgConnection:
    """
    Obtiene una conexión del pool. El llamador DEBE devolver la conexión
    usando release_connection(conn) en un bloque finally.
    """
    _init_pool()
    try:
        conn = _db_pool.getconn()
        conn.set_client_encoding("UTF8")
        return conn
    except Error as e:
        logger.error(f"❌ Error al obtener conexión del pool: {e}")
        raise


def release_connection(conn: Optional[PgConnection]) -> None:
    """
    Devuelve una conexión al pool. Debe llamarse SIEMPRE en el bloque finally.
    """
    if conn and _db_pool and not _db_pool.closed:
        try:
            _db_pool.putconn(conn)
        except Exception:
            pass


def close_pool() -> None:
    """
    Cierra todas las conexiones del pool. Llamar al apagar la aplicación.
    """
    global _db_pool
    if _db_pool and not _db_pool.closed:
        _db_pool.closeall()
        logger.info("Pool de conexiones cerrado")
        _db_pool = None


def get_credentials_scraping() -> Optional[Dict]:
    """
    Obtiene las credenciales activas para scraping desde la tabla `login`.
    Desencripta el campo password_enc usando la ENCRYPTION_KEY de entorno.
    Retorna dict con url, usuario, password, tipo_usuario, login_id o None.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, url_plataforma, usuario, password_enc, tipo_usuario
            FROM login
            WHERE activo = TRUE
            ORDER BY updated_at DESC
            LIMIT 1;
        """)
        row = cursor.fetchone()
        if not row:
            logger.warning("⚠️  No se encontraron credenciales activas en la tabla login.")
            return None

        login_id, url, usuario, password_enc, tipo_usuario = row

        # Desencriptar contraseña
        fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
        password = fernet.decrypt(password_enc.encode()).decode()

        return {
            "login_id": login_id,
            "url": url,
            "usuario": usuario,
            "password": password,
            "tipo_usuario": tipo_usuario,
        }
    except Exception as e:
        logger.error(f"Error obteniendo credenciales de scraping: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)


def registrar_credencial(url: str, usuario: str, password: str, tipo_usuario: str = "Administrativo") -> Dict:
    """
    Inserta una credencial nueva en la tabla login, cifrando la contraseña.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
        password_enc = fernet.encrypt(password.encode()).decode()

        cursor.execute("""
            INSERT INTO login (url_plataforma, usuario, password_enc, tipo_usuario)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (url, usuario, password_enc, tipo_usuario))

        login_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "ok", "login_id": login_id, "message": "Credencial registrada correctamente."}
    except Exception as e:
        logger.error(f"Error registrando credencial: {e}")
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)
