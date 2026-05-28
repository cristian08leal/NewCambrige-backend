# =============================================================================
# modules/db_estudiantes.py — Operaciones de base de datos para estudiantes (COD-01, COD-03)
# =============================================================================

from typing import List, Dict, Optional
from psycopg2.extensions import cursor as PgCursor
from utils.logger import get_logger
from config.settings import GRADO_ID_DEFAULT
from config.constants import GRADOS_VALIDOS, JORNADAS_VALIDAS
from modules.db_pool import get_connection, release_connection
from modules.db_ejecuciones import registrar_inicio_ejecucion, registrar_fin_ejecucion

logger = get_logger("db_estudiantes")


import unicodedata

def get_or_create_grado_id(cursor: PgCursor, nombre: str) -> int:
    """Obtiene el grado_id de un grado por nombre o lo crea dinámicamente si no existe (ignorando tildes)."""
    if not nombre or not nombre.strip():
        return GRADO_ID_DEFAULT
    
    nombre_clean = nombre.strip()
    nombre_norm = ''.join(c for c in unicodedata.normalize('NFD', nombre_clean) if unicodedata.category(c) != 'Mn').upper()

    cursor.execute("SELECT grado_id, nombre FROM grados")
    existing = cursor.fetchall()
    
    for gid, gnom in existing:
        if not gnom: continue
        gnom_norm = ''.join(c for c in unicodedata.normalize('NFD', gnom) if unicodedata.category(c) != 'Mn').upper()
        if gnom_norm == nombre_norm:
            return gid
            
    cursor.execute("INSERT INTO grados (nombre) VALUES (%s) RETURNING grado_id", (nombre_clean,))
    return cursor.fetchone()[0]


def get_or_create_jornada_id(cursor: PgCursor, nombre: str) -> int:
    """Obtiene el jornada_id de una jornada por nombre o lo crea dinámicamente si no existe."""
    if not nombre or not nombre.strip():
        cursor.execute("SELECT id FROM jornadas LIMIT 1")
        return cursor.fetchone()[0]
    nombre_clean = nombre.strip()
    cursor.execute("SELECT id FROM jornadas WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(%s))", (nombre_clean,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO jornadas (nombre) VALUES (%s) RETURNING id", (nombre_clean,))
    return cursor.fetchone()[0]


def obtener_estudiantes(limit=100) -> List[Dict]:
    """Obtiene los estudiantes con LEFT JOINs para resolver grado, jornada y titular dinámicamente."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT 
                e.estudiante_id AS id, 
                e.documento, 
                e.nombre, 
                g.nombre AS grado_texto, 
                e.curso, 
                d.nombre AS titular, 
                j.nombre AS jornada,
                e.codigo_interno
            FROM estudiantes e
            LEFT JOIN grados g ON e.grado_id = g.grado_id
            LEFT JOIN jornadas j ON e.jornada_id = j.id
            LEFT JOIN asignaciones a ON e.grado_id = a.grado_id AND UPPER(TRIM(e.curso)) = UPPER(TRIM(a.curso)) AND a.vigente = TRUE
            LEFT JOIN docentes d ON a.docente_id = d.id
            ORDER BY e.estudiante_id DESC 
            LIMIT %s;
        """
        cursor.execute(sql, (limit,))
        columnas = [desc[0] for desc in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error obteniendo estudiantes: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)


def verificar_duplicado(tipo: str, codigo_interno: Optional[str], documento: Optional[str], cursor: Optional[PgCursor] = None) -> Optional[Dict]:
    """
    Verifica si existe un registro con el mismo codigo_interno o documento.
    Funciona tanto para estudiantes como para docentes. Reutiliza el cursor si se provee.
    """
    conn = None
    own_cursor = False
    try:
        if cursor is None:
            conn = get_connection()
            cursor = conn.cursor()
            own_cursor = True

        if tipo == "estudiante":
            sql = """
                SELECT 
                    e.estudiante_id AS id, 
                    e.nombre, 
                    e.documento, 
                    e.codigo_interno, 
                    g.nombre AS grado_texto, 
                    e.curso, 
                    j.nombre AS jornada
                FROM estudiantes e
                LEFT JOIN grados g ON e.grado_id = g.grado_id
                LEFT JOIN jornadas j ON e.jornada_id = j.id
                WHERE e.documento = %s OR (e.codigo_interno = %s AND e.codigo_interno IS NOT NULL)
                LIMIT 1;
            """
        else:  # docente
            sql = """
                SELECT 
                    d.id, 
                    d.nombre, 
                    d.documento, 
                    d.codigo_interno,
                    g.nombre AS grado_titular,
                    a.curso AS curso_titular
                FROM docentes d
                LEFT JOIN asignaciones a ON d.id = a.docente_id AND a.vigente = TRUE
                LEFT JOIN grados g ON a.grado_id = g.grado_id
                WHERE d.documento = %s OR (d.codigo_interno = %s AND d.codigo_interno IS NOT NULL)
                LIMIT 1;
            """

        params = [documento or None, codigo_interno or None]
        cursor.execute(sql, params)
        row = cursor.fetchone()
        if row:
            col_names = [desc[0] for desc in cursor.description]
            return dict(zip(col_names, row))
        return None
    except Exception as e:
        logger.error(f"Error verificando duplicado para {tipo}: {e}")
        return None
    finally:
        if own_cursor:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)


def insertar_o_actualizar_persona(tipo: str, datos: Dict) -> Dict:
    """Inserta o actualiza un registro individual de estudiante o docente."""
    conn = None
    cursor = None

    nombre = (datos.get("nombre") or "").strip()
    codigo_interno = (datos.get("codigo_interno") or "").strip() or None
    documento = (datos.get("documento_nacional") or datos.get("documento") or "").strip() or None

    # Regla de duplicación de identificadores
    if codigo_interno and not documento:
        documento = codigo_interno
    elif documento and not codigo_interno:
        codigo_interno = documento

    if not nombre:
        return {"status": "error", "message": "El nombre es obligatorio.", "action": None}

    if not documento and not codigo_interno:
        return {"status": "error", "message": "Debes ingresar al menos el código interno o el documento nacional.", "action": None}

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if tipo == "estudiante":
            grado = (datos.get("grado") or "").strip()
            curso = (datos.get("curso") or "").strip()
            jornada = (datos.get("jornada") or "").strip()

            if not grado:
                return {"status": "error", "message": "El grado es obligatorio para estudiantes.", "action": None}
            if not curso:
                return {"status": "error", "message": "El curso/grupo es obligatorio para estudiantes.", "action": None}
            if not jornada:
                return {"status": "error", "message": "La jornada es obligatoria para estudiantes.", "action": None}

            grado_id = get_or_create_grado_id(cursor, grado)
            jornada_id = get_or_create_jornada_id(cursor, jornada)

            sql = """
                INSERT INTO estudiantes (
                    grado_id, jornada_id, nombre, documento, codigo_interno, curso, activo, fecha_activo
                )
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                ON CONFLICT (documento) DO UPDATE SET
                    grado_id = EXCLUDED.grado_id,
                    jornada_id = EXCLUDED.jornada_id,
                    nombre = EXCLUDED.nombre,
                    codigo_interno = EXCLUDED.codigo_interno,
                    curso = EXCLUDED.curso
                RETURNING estudiante_id, (xmax = 0) AS is_insert;
            """
            cursor.execute(sql, (grado_id, jornada_id, nombre, documento, codigo_interno, curso))

        else:  # docente
            sql = """
                INSERT INTO docentes (documento, codigo_interno, nombre, activo, fecha_actualizacion)
                VALUES (%s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                ON CONFLICT (documento) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    codigo_interno = EXCLUDED.codigo_interno,
                    fecha_actualizacion = CURRENT_TIMESTAMP
                RETURNING id, (xmax = 0) AS is_insert;
            """
            cursor.execute(sql, (documento, codigo_interno, nombre))
            
            result = cursor.fetchone()
            docente_id = result[0] if result else None
            is_insert = result[1] if result else True
            
            grado = (datos.get("grado") or "").strip()
            curso = (datos.get("curso") or "").strip()
            
            if docente_id and grado and curso:
                grado_id = get_or_create_grado_id(cursor, grado)
                # Actualizar asignación titular
                cursor.execute("UPDATE asignaciones SET vigente = FALSE WHERE docente_id = %s;", (docente_id,))
                cursor.execute("""
                    INSERT INTO asignaciones (docente_id, grado_id, curso, vigente)
                    VALUES (%s, %s, %s, TRUE)
                    ON CONFLICT (docente_id, grado_id, curso, vigente) DO UPDATE SET vigente = TRUE;
                """, (docente_id, grado_id, curso))

        if tipo == "estudiante":
            result = cursor.fetchone()
            is_insert = result[1] if result else True

        conn.commit()
        action = "created" if is_insert else "updated"
        msg = "Registro guardado correctamente." if is_insert else "Registro actualizado correctamente."
        return {"status": "ok", "message": msg, "action": action}

    except Exception as e:
        logger.error(f"Error insertando/actualizando persona: {e}")
        if conn:
            conn.rollback()
        return {"status": "error", "message": f"Error de base de datos: {str(e)}", "action": None}
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)


def procesar_importacion_masiva(tipo: str, registros: List[Dict]) -> Dict:
    """
    COD-03: Procesa un lote de registros de forma tolerante a fallos.
    Si una fila falla, se registra el error específico pero se continúan
    procesando los demás registros usando SAVEPOINTs individuales.
    """
    conn = None
    cursor = None
    log = []
    total_ok = 0

    try:
        conn = get_connection()
        cursor = conn.cursor()

        for i, reg in enumerate(registros):
            fila_num = i + 1
            nombre = (reg.get("nombre") or "").strip()
            codigo_interno = (reg.get("codigo_interno") or "").strip() or None
            documento = (reg.get("documento_nacional") or reg.get("documento") or "").strip() or None

            # Regla de duplicación
            if codigo_interno and not documento:
                documento = codigo_interno
            elif documento and not codigo_interno:
                codigo_interno = documento

            # Validar campos básicos locales
            if not nombre:
                log.append({
                    "fila": fila_num,
                    "nombre": "(vacío)",
                    "estado": "rechazado",
                    "razon": "nombre vacío"
                })
                continue

            if not documento and not codigo_interno:
                log.append({
                    "fila": fila_num,
                    "nombre": nombre,
                    "estado": "rechazado",
                    "razon": "falta documento y código interno"
                })
                continue

            # Crear SAVEPOINT individual para la fila
            savepoint_name = f"import_row_{fila_num}"
            cursor.execute(f"SAVEPOINT {savepoint_name}")

            try:
                if tipo == "estudiante":
                    grado = (reg.get("grado") or "").strip()
                    curso = (reg.get("curso") or "").strip()
                    jornada = (reg.get("jornada") or "").strip()

                    # Validaciones locales específicas
                    if not grado:
                        raise ValueError("grado vacío")
                    if not jornada:
                        raise ValueError("jornada vacía")
                    if not curso:
                        raise ValueError("curso/grupo vacío")

                    grado_id = get_or_create_grado_id(cursor, grado)
                    jornada_id = get_or_create_jornada_id(cursor, jornada)

                    # Verificar si existe duplicado para poner el estado correcto en el log
                    exists = verificar_duplicado("estudiante", codigo_interno, documento, cursor=cursor)

                    sql = """
                        INSERT INTO estudiantes (
                            grado_id, jornada_id, nombre, documento, codigo_interno, curso, activo, fecha_activo
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                        ON CONFLICT (documento) DO UPDATE SET
                            grado_id = EXCLUDED.grado_id,
                            jornada_id = EXCLUDED.jornada_id,
                            nombre = EXCLUDED.nombre,
                            codigo_interno = EXCLUDED.codigo_interno,
                            curso = EXCLUDED.curso;
                    """
                    cursor.execute(sql, (grado_id, jornada_id, nombre, documento, codigo_interno, curso))

                    if exists:
                        log.append({"fila": fila_num, "nombre": nombre, "estado": "actualizado", "razon": None})
                    else:
                        log.append({"fila": fila_num, "nombre": nombre, "estado": "admitido", "razon": None})
                    total_ok += 1

                else:  # docente
                    grado = (reg.get("grado") or "").strip()
                    curso = (reg.get("curso") or "").strip()

                    exists = verificar_duplicado("docente", codigo_interno, documento, cursor=cursor)

                    sql = """
                        INSERT INTO docentes (documento, codigo_interno, nombre, activo, fecha_actualizacion)
                        VALUES (%s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                        ON CONFLICT (documento) DO UPDATE SET
                            nombre = EXCLUDED.nombre,
                            codigo_interno = EXCLUDED.codigo_interno,
                            fecha_actualizacion = CURRENT_TIMESTAMP
                        RETURNING id;
                    """
                    cursor.execute(sql, (documento, codigo_interno, nombre))
                    docente_id = cursor.fetchone()[0]

                    if grado and curso:
                        grado_id = get_or_create_grado_id(cursor, grado)
                        # Desactivar anteriores asignaciones
                        cursor.execute("UPDATE asignaciones SET vigente = FALSE WHERE docente_id = %s;", (docente_id,))
                        cursor.execute("""
                            INSERT INTO asignaciones (docente_id, grado_id, curso, vigente)
                            VALUES (%s, %s, %s, TRUE)
                            ON CONFLICT (docente_id, grado_id, curso, vigente) DO UPDATE SET vigente = TRUE;
                        """, (docente_id, grado_id, curso))

                    if exists:
                        log.append({"fila": fila_num, "nombre": nombre, "estado": "actualizado", "razon": None})
                    else:
                        log.append({"fila": fila_num, "nombre": nombre, "estado": "admitido", "razon": None})
                    total_ok += 1

                cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")

            except Exception as e:
                cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                log.append({
                    "fila": fila_num,
                    "nombre": nombre,
                    "estado": "rechazado",
                    "razon": str(e)
                })

        conn.commit()
        return {
            "status": "completed",
            "log": log,
            "total_ok": total_ok,
            "total_rechazados": len(registros) - total_ok,
            "message": f"Proceso completado. {total_ok} de {len(registros)} registros cargados exitosamente."
        }

    except Exception as e:
        logger.error(f"Error en importación masiva: {e}")
        if conn:
            conn.rollback()
        return {
            "status": "error",
            "log": log,
            "total_ok": total_ok,
            "total_rechazados": len(registros) - total_ok,
            "message": f"Error crítico de base de datos: {str(e)}"
        }
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)


def insertar_estudiantes(estudiantes: List[Dict], exec_id: Optional[int] = None) -> Dict:
    """Inserta estudiantes procesados del scraper (Playwright) usando Tablas de Staging y Fusión Relacional."""
    if not estudiantes:
        logger.warning("⚠️  Lista de estudiantes vacía. No hay nada que insertar.")
        return {"insertados": 0, "actualizados": 0, "conflictos": 0, "errores": 0, "detalles": []}

    from datetime import datetime
    from psycopg2.extras import execute_values
    conn = None
    cursor = None
    insertados = 0
    actualizados = 0
    conflictos = 0
    errores = 0
    detalles_log = []

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Si no se pasó exec_id, crear uno para la ejecución
        if exec_id is None:
            exec_id = registrar_inicio_ejecucion(cursor, tipo="estudiantes")
            conn.commit()

        # 1. Truncar tabla de staging
        cursor.execute("TRUNCATE TABLE staging_estudiantes;")

        # 2. Filtrar y preparar registros para staging
        records_to_insert = []
        for est in estudiantes:
            codigo_interno = est.get("codigo_interno")
            if codigo_interno: codigo_interno = str(codigo_interno).strip()
            
            documento = est.get("documento")
            if documento: documento = str(documento).strip()
            
            nombre = est.get("nombre", "").strip()
            jornada = est.get("jornada", "").strip()
            grado_texto = est.get("grado_texto", "").strip()
            curso = est.get("curso", "").strip()

            if not nombre:
                logger.warning(f"⚠️  Registro sin nombre omitido: {est}")
                errores += 1
                continue

            if not codigo_interno and not documento:
                detalles_log.append({
                    "codigo": codigo_interno, "documento": documento, "accion": "RECHAZADO",
                    "motivo": "No tiene código ni documento", "timestamp": datetime.now().isoformat()
                })
                errores += 1
                continue
                
            # Fallback de identificadores
            if not documento and codigo_interno:
                documento = codigo_interno
            elif not codigo_interno and documento:
                codigo_interno = documento

            if len(nombre) > 150:
                nombre = nombre[:150]

            records_to_insert.append((documento, codigo_interno, nombre, grado_texto, curso, jornada))

        # 3. Inserción masiva en staging_estudiantes
        if records_to_insert:
            execute_values(
                cursor,
                "INSERT INTO staging_estudiantes (documento, codigo_interno, nombre, grado, curso, jornada) VALUES %s",
                records_to_insert
            )

        # 4. Fusión (UPSERT) con la tabla productiva de estudiantes
        merge_sql = """
            INSERT INTO estudiantes (grado_id, jornada_id, nombre, documento, codigo_interno, curso, activo)
            SELECT DISTINCT ON (se.documento)
                COALESCE(g.grado_id, 1) AS grado_id,
                COALESCE(j.id, 1)       AS jornada_id,
                se.nombre,
                se.documento,
                se.codigo_interno,
                se.curso,
                TRUE
            FROM staging_estudiantes se
            LEFT JOIN grados g ON UPPER(TRIM(se.grado)) = UPPER(TRIM(g.nombre))
            LEFT JOIN jornadas j ON UPPER(TRIM(se.jornada)) = UPPER(TRIM(j.nombre))
            ORDER BY se.documento
            ON CONFLICT (documento) 
            DO UPDATE SET
                grado_id = EXCLUDED.grado_id,
                jornada_id = EXCLUDED.jornada_id,
                nombre = EXCLUDED.nombre,
                codigo_interno = EXCLUDED.codigo_interno,
                curso = EXCLUDED.curso,
                activo = TRUE,
                updated_at = CURRENT_TIMESTAMP
            RETURNING documento, codigo_interno, (xmax = 0) AS is_insert;
        """
        cursor.execute(merge_sql)
        results = cursor.fetchall()
        for doc, cod, is_insert in results:
            if is_insert:
                insertados += 1
                detalles_log.append({
                    "codigo": cod, "documento": doc, "accion": "INSERT",
                    "motivo": "Nuevo registro insertado desde staging", "timestamp": datetime.now().isoformat()
                })
            else:
                actualizados += 1
                detalles_log.append({
                    "codigo": cod, "documento": doc, "accion": "UPDATE",
                    "motivo": "Registro actualizado desde staging", "timestamp": datetime.now().isoformat()
                })

        # 5. Soft-Delete (Baja lógica de estudiantes omitidos)
        soft_delete_sql = """
            UPDATE estudiantes
            SET activo = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE activo = TRUE
              AND documento NOT IN (SELECT documento FROM staging_estudiantes)
            RETURNING documento, codigo_interno;
        """
        cursor.execute(soft_delete_sql)
        deactivated = cursor.fetchall()
        for doc, cod in deactivated:
            detalles_log.append({
                "codigo": cod, "documento": doc, "accion": "DESACTIVADO",
                "motivo": "Estudiante no presente en el scraping activo (Baja lógica)", "timestamp": datetime.now().isoformat()
            })

        registrar_fin_ejecucion(cursor, exec_id, insertados, actualizados, errores)
        conn.commit()
        logger.info(
            f"📊 Resumen ETL Estudiantes (Staging) → Insertados: {insertados} | "
            f"Actualizados: {actualizados} | Desactivados: {len(deactivated)} | Errores: {errores}"
        )

    except Exception as e:
        logger.error(f"❌ Error durante la inserción en PostgreSQL (Staging): {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)
    return {"insertados": insertados, "actualizados": actualizados, "conflictos": conflictos, "errores": errores, "detalles": detalles_log}
