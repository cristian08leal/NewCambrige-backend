# =============================================================================
# modules/db_ejecuciones.py — Trazabilidad y estado de ejecuciones del bot (API-01, SEG-06)
# =============================================================================

from typing import Dict, Optional, List
from psycopg2.extensions import cursor as PgCursor
from utils.logger import get_logger
from modules.db_pool import get_connection, release_connection

logger = get_logger("db_ejecuciones")


def registrar_inicio_ejecucion(cursor: PgCursor, tipo: Optional[str] = None, login_id: Optional[int] = None) -> int:
    """
    Crea un registro en `bot_ejecuciones` para trazabilidad de ejecuciones.
    Retorna el ID de la ejecución.
    """
    sql = """
        INSERT INTO bot_ejecuciones (estado, tipo, login_id)
        VALUES ('iniciado', %s, %s)
        RETURNING id;
    """
    cursor.execute(sql, (tipo, login_id))
    return cursor.fetchone()[0]


def registrar_fin_ejecucion(cursor: PgCursor, exec_id: int, insertados: int, omitidos: int, errores: int, estado: str = 'finalizado') -> None:
    """
    Actualiza el registro de ejecución con los resultados finales.
    """
    sql = """
        UPDATE bot_ejecuciones 
        SET fecha_fin = CURRENT_TIMESTAMP,
            insertados = %s,
            omitidos = %s,
            errores = %s,
            estado = %s
        WHERE id = %s;
    """
    cursor.execute(sql, (insertados, omitidos, errores, estado, exec_id))


def obtener_estado_scraping() -> Dict:
    """
    API-01: Consulta el estado del scraping desde la tabla bot_ejecuciones.
    Retorna el estado de la última ejecución activa (fecha_fin IS NULL).
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, estado, tipo, fecha_inicio
            FROM bot_ejecuciones
            WHERE fecha_fin IS NULL AND estado = 'iniciado'
            ORDER BY fecha_inicio DESC
            LIMIT 1;
        """)
        row = cursor.fetchone()
        if row:
            return {
                "running": True,
                "tipo": row[2],
                "exec_id": row[0],
                "fecha_inicio": row[3].isoformat() if row[3] else None,
            }
        return {"running": False, "tipo": None}
    except Exception as e:
        logger.error(f"Error consultando estado de scraping: {e}")
        return {"running": False, "tipo": None, "error": str(e)}
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)


def marcar_ejecuciones_interrumpidas() -> None:
    """
    API-01/OPS: Al arrancar el servidor, marca como 'interrumpido' cualquier
    ejecución que haya quedado con fecha_fin IS NULL (por un reinicio forzado).
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bot_ejecuciones
            SET estado = 'interrumpido', fecha_fin = CURRENT_TIMESTAMP
            WHERE fecha_fin IS NULL AND estado = 'iniciado';
        """)
        afectados = cursor.rowcount
        conn.commit()
        if afectados > 0:
            logger.warning(f"⚠️  {afectados} ejecución(es) marcada(s) como 'interrumpido' tras reinicio del servidor.")
    except Exception as e:
        logger.error(f"Error marcando ejecuciones interrumpidas: {e}")
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

def obtener_historial_ejecuciones(limit: int = 20, offset: int = 0, tipo: Optional[str] = None, estado: Optional[str] = None) -> List[Dict]:
    conn = None
    cursor = None
    try:
        from modules.db_pool import get_connection, release_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM bot_ejecuciones WHERE 1=1'
        params = []
        if tipo:
            query += ' AND tipo = %s'
            params.append(tipo)
        if estado:
            query += ' AND estado = %s'
            params.append(estado)
            
        query += ' ORDER BY fecha_inicio DESC LIMIT %s OFFSET %s'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f'Error obteniendo historial ejecuciones: {e}')
        return []
    finally:
        if cursor: cursor.close()
        if conn: release_connection(conn)