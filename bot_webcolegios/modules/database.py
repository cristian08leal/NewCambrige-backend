# =============================================================================
# modules/database.py — Fachada unificada del módulo de base de datos (COD-01)
# =============================================================================
# Importa y re-exporta todas las funciones públicas de los submódulos cohesivos
# para garantizar 100% de compatibilidad con importaciones existentes.
# =============================================================================

# 1. Pool y credenciales (db_pool)
from modules.db_pool import (
    get_connection,
    release_connection,
    close_pool,
    get_credentials_scraping,
    registrar_credencial,
)

# 2. Trazabilidad de ejecuciones (db_ejecuciones)
from modules.db_ejecuciones import (
    registrar_inicio_ejecucion,
    registrar_fin_ejecucion,
    obtener_estado_scraping,
    marcar_ejecuciones_interrumpidas,
    obtener_historial_ejecuciones,
)

# 3. Estudiantes e Importaciones (db_estudiantes)
from modules.db_estudiantes import (
    obtener_estudiantes,
    verificar_duplicado,
    insertar_o_actualizar_persona,
    procesar_importacion_masiva,
    insertar_estudiantes,
)

# 4. Docentes y Grupos (db_docentes)
from modules.db_docentes import (
    obtener_docentes,
    insertar_docentes,
    obtener_grupos,
    agregar_grupo,
)
