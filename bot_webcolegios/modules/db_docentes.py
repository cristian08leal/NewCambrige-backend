# =============================================================================
# modules/db_docentes.py — Operaciones de base de datos para docentes (COD-01)
# =============================================================================

from typing import List, Dict, Optional
from utils.logger import get_logger
from modules.db_pool import get_connection, release_connection
from modules.db_ejecuciones import registrar_inicio_ejecucion, registrar_fin_ejecucion
from modules.db_estudiantes import get_or_create_grado_id

logger = get_logger("db_docentes")


def obtener_docentes(limit: int = 100) -> List[Dict]:
    """
    Obtiene los docentes resolviendo el grado y curso titular dinámicamente.

    Args:
        limit: Número máximo de registros a obtener
    Returns:
        Lista de diccionarios con la información de docentes
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT 
                d.id, 
                d.documento, 
                d.nombre, 
                g.nombre AS grado_titular, 
                a.curso AS curso_titular
            FROM docentes d
            LEFT JOIN asignaciones a ON d.id = a.docente_id AND a.vigente = TRUE
            LEFT JOIN grados g ON a.grado_id = g.grado_id
            ORDER BY d.id DESC 
            LIMIT %s;
        """
        cursor.execute(sql, (limit,))
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error obteniendo docentes: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)


def insertar_docentes(docentes: List[Dict], exec_id: Optional[int] = None) -> Dict:
    """Inserta o actualiza docentes y sus asignaciones usando Tablas de Staging y Fusión Relacional."""
    if not docentes:
        logger.warning("⚠️  Lista de docentes vacía. No hay nada que insertar.")
        return {"insertados": 0, "omitidos": 0, "errores": 0}

    from psycopg2.extras import execute_values
    conn = None
    cursor = None
    insertados = 0
    omitidos = 0
    errores = 0

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if exec_id is None:
            exec_id = registrar_inicio_ejecucion(cursor, tipo="docentes")
            conn.commit()

        # 1. Truncar tabla de staging
        cursor.execute("TRUNCATE TABLE staging_docentes;")

        # 2. Filtrar y preparar registros para staging
        records_to_insert = []
        for doc_info in docentes:
            doc = doc_info.get("documento", "").strip()
            nombre = doc_info.get("nombre", "").strip()
            codigo_interno = doc_info.get("codigo_interno", "").strip() or None
            grado_titular = doc_info.get("grado_titular", "").strip() or None
            curso_titular = doc_info.get("curso_titular", "").strip() or None

            # Fallback de identificadores si faltan
            if not doc and codigo_interno:
                doc = codigo_interno
            elif not codigo_interno and doc:
                codigo_interno = doc

            if not doc or not nombre:
                logger.warning(f"⚠️  Registro de docente inválido omitido: {doc_info}")
                errores += 1
                continue

            records_to_insert.append((doc, codigo_interno, nombre, grado_titular, curso_titular))

        # 3. Inserción masiva en staging_docentes
        if records_to_insert:
            execute_values(
                cursor,
                "INSERT INTO staging_docentes (documento, codigo_interno, nombre, grado_titular, curso_titular) VALUES %s",
                records_to_insert
            )

        # 4. Fusión (UPSERT) con la tabla productiva de docentes
        merge_doc_sql = """
            INSERT INTO docentes (documento, codigo_interno, nombre, activo, fecha_actualizacion)
            SELECT DISTINCT ON (sd.documento)
                sd.documento,
                sd.codigo_interno,
                sd.nombre,
                TRUE,
                CURRENT_TIMESTAMP
            FROM staging_docentes sd
            ORDER BY sd.documento
            ON CONFLICT (documento) 
            DO UPDATE SET
                nombre = EXCLUDED.nombre,
                codigo_interno = EXCLUDED.codigo_interno,
                fecha_actualizacion = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, (xmax = 0) AS is_insert;
        """
        cursor.execute(merge_doc_sql)
        results = cursor.fetchall()
        for doc_id, is_insert in results:
            if is_insert:
                insertados += 1
            else:
                omitidos += 1

        # 5. Soft-Delete (Baja lógica de docentes omitidos)
        soft_delete_sql = """
            UPDATE docentes
            SET activo = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE activo = TRUE
              AND documento NOT IN (SELECT documento FROM staging_docentes);
        """
        cursor.execute(soft_delete_sql)

        # 6. Sincronizar asignaciones titulares
        # Marcar asignaciones previas vigentes como inactivas
        cursor.execute("UPDATE asignaciones SET vigente = FALSE WHERE vigente = TRUE;")

        # Registrar asignaciones activas de los docentes procesados
        merge_asig_sql = """
            INSERT INTO asignaciones (docente_id, grado_id, curso, vigente)
            SELECT DISTINCT ON (d.id, g.grado_id, sd.curso_titular)
                d.id,
                g.grado_id,
                sd.curso_titular,
                TRUE
            FROM staging_docentes sd
            INNER JOIN docentes d ON sd.documento = d.documento
            INNER JOIN grados g ON UPPER(TRIM(sd.grado_titular)) = UPPER(TRIM(g.nombre))
            WHERE sd.grado_titular IS NOT NULL AND sd.curso_titular IS NOT NULL
            ORDER BY d.id, g.grado_id, sd.curso_titular
            ON CONFLICT (docente_id, grado_id, curso, vigente) 
            DO UPDATE SET vigente = TRUE;
        """
        cursor.execute(merge_asig_sql)

        registrar_fin_ejecucion(cursor, exec_id, insertados, omitidos, errores)
        conn.commit()
        logger.info(f"📊 Resumen Docentes (Staging) → Insertados: {insertados} | Omitidos: {omitidos} | Errores: {errores}")

    except Exception as e:
        logger.error(f"❌ Error durante la inserción de docentes (Staging): {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

    return {"insertados": insertados, "omitidos": omitidos, "errores": errores}


def obtener_grupos() -> Dict[str, List[str]]:
    """
    Retorna todos los grupos por grado resolviendo grado dinámicamente.

    Args:
        None
    Returns:
        Diccionario con grados como llaves y lista de grupos como valores
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT g.nombre AS grado, gr.grupo 
            FROM grupos gr
            JOIN grados g ON gr.grado_id = g.grado_id
            ORDER BY g.nombre, gr.grupo;
        """
        cursor.execute(sql)
        result = {}
        for grado, grupo in cursor.fetchall():
            if grado not in result:
                result[grado] = []
            result[grado].append(grupo)
        return result
    except Exception as e:
        logger.error(f"Error obteniendo grupos: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)


def agregar_grupo(grado: str, grupo: str) -> Dict:
    """
    Añade un grupo a un grado resolviendo grado_id dinámicamente.

    Args:
        grado: Nombre del grado
        grupo: Nombre del grupo/curso a añadir
    Returns:
        Diccionario con el estado de la operación y el mensaje
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        grado_id = get_or_create_grado_id(cursor, grado)
        
        cursor.execute(
            "INSERT INTO grupos (grado_id, grupo) VALUES (%s, %s) ON CONFLICT (grado_id, grupo) DO NOTHING RETURNING id;",
            (grado_id, grupo)
        )
        inserted = cursor.fetchone()
        conn.commit()
        if inserted:
            return {"status": "ok", "message": f"Grupo {grupo} añadido a {grado}."}
        else:
            return {"status": "ok", "message": f"El grupo {grupo} ya existe en {grado}."}
    except Exception as e:
        logger.error(f"Error añadiendo grupo: {e}")
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)
