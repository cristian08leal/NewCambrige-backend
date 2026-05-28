# =============================================================================
# app.py — Servidor FastAPI y API de Control de WebColegios Bot (SEG-05, SEG-06, API-02)
# =============================================================================

import os
from contextlib import asynccontextmanager
from typing import List, Dict, Optional
from fastapi import FastAPI, Request, BackgroundTasks, Depends, Header, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator, validator, Field

from main import run_scrape_estudiantes, run_scrape_docentes
from config.settings import API_KEY
from modules.database import (
    obtener_estudiantes, obtener_docentes, get_connection, release_connection,
    verificar_duplicado, insertar_o_actualizar_persona,
    procesar_importacion_masiva, obtener_grupos, agregar_grupo,
    obtener_estado_scraping, marcar_ejecuciones_interrumpidas,
    registrar_inicio_ejecucion, registrar_fin_ejecucion, close_pool,
    get_credentials_scraping, obtener_historial_ejecuciones,
)


# =============================================================================
# Lifespan: init/teardown del pool y limpieza de estado (API-01 / OPS-01)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Al arrancar: marca ejecuciones huérfanas como 'interrumpido'.
    Al cerrar: cierra el pool de conexiones limpiamente.
    """
    marcar_ejecuciones_interrumpidas()
    yield
    close_pool()


app = FastAPI(
    title="WebColegios Bot API",
    description="API de control para la sincronización de datos con WebColegios. Permite extracción automatizada (scraping), importaciones manuales y trazabilidad de ejecuciones.",
    version="1.0.0",
    lifespan=lifespan
)

# Servir archivos estáticos de React
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static_react")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")


# Dependency de seguridad para API Key (SEG-05)
async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Verifica que el header X-API-Key contenga la API_KEY del sistema."""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o ausente en el header X-API-Key."
        )


@app.get("/", response_class=HTMLResponse)
async def read_root():
    idx = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return HTMLResponse("<h1>Frontend no compilado. Ejecuta: cd frontend && npm run build</h1>", status_code=503)


# =============================================================================
# Endpoint de Salud (API-02)
# =============================================================================

@app.get("/api/health", summary="Verificar salud del sistema", description="Endpoint de monitoreo activo de salud para la base de datos y el servidor. Devuelve 200 si todo está operativo o 503 si hay falla en BD.")
async def health_check():
    """Endpoint de monitoreo activo de salud para la base de datos y el servidor."""
    db_status = "healthy"
    detail = "El servidor y la base de datos están operativos."
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
    except Exception as e:
        db_status = "unhealthy"
        detail = f"Fallo de conexión a la base de datos: {e}"
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": db_status, "detail": detail}
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)
            
    return {"status": "ok", "database": db_status, "detail": detail}


# =============================================================================
# Scraping con estado persistente en BD (API-01, SEG-06)
# =============================================================================

@app.post("/api/scrape/{tipo}", dependencies=[Depends(verify_api_key)], summary="Iniciar Scraping", description="Inicia un proceso de extracción en segundo plano para 'estudiantes' o 'docentes'. Registra la ejecución en BD.")
async def start_scrape(tipo: str, background_tasks: BackgroundTasks):
    """Inicia el proceso de scraping protegido por API Key (SEG-05, SEG-06)."""
    # Consultar si hay un scraping en curso desde la BD
    estado = obtener_estado_scraping()
    if estado.get("running"):
        return JSONResponse(
            {"status": "error", "message": "Ya hay un scraping en ejecución"},
            status_code=400,
        )

    if tipo not in ["estudiantes", "docentes"]:
        return JSONResponse({"status": "error", "message": "Tipo inválido"}, status_code=400)

    # Limpiar log anterior
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/bot.log", "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass

    # Registrar inicio de ejecución en la BD con login_id activo (SEG-06)
    conn = None
    cursor = None
    exec_id = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener credenciales activas para extraer el login_id (SEG-06)
        creds = get_credentials_scraping()
        login_id = creds.get("login_id") if creds else None
        
        exec_id = registrar_inicio_ejecucion(cursor, tipo=tipo, login_id=login_id)
        conn.commit()
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"Error registrando ejecución: {e}"},
            status_code=500,
        )
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

    def task():
        try:
            if tipo == "estudiantes":
                run_scrape_estudiantes(exec_id=exec_id)
            elif tipo == "docentes":
                run_scrape_docentes(exec_id=exec_id)
        except Exception:
            pass
        finally:
            # Marcar finalización si no la marcó ya el propio insertar_*
            try:
                c = get_connection()
                cur = c.cursor()
                # Solo actualizar si sigue como 'iniciado' (no fue ya cerrado por insertar_*)
                cur.execute("""
                    UPDATE bot_ejecuciones
                    SET estado = 'finalizado', fecha_fin = CURRENT_TIMESTAMP
                    WHERE id = %s AND fecha_fin IS NULL;
                """, (exec_id,))
                c.commit()
                cur.close()
                release_connection(c)
            except Exception:
                pass

    background_tasks.add_task(task)
    return {"status": "ok", "message": f"Scraping de {tipo} iniciado", "exec_id": exec_id}


@app.get("/api/ejecuciones", summary="Historial de Ejecuciones", description="Obtiene el registro paginado de las tareas del bot, útil para auditoría y visualización de progreso.")
async def get_ejecuciones(limit: int = 20, offset: int = 0, tipo: Optional[str] = None, estado: Optional[str] = None):
    """API-04: Retorna el historial paginado de ejecuciones."""
    historial = obtener_historial_ejecuciones(limit=limit, offset=offset, tipo=tipo, estado=estado)
    return {"data": historial}

@app.get("/api/status", summary="Estado del Scraping", description="Devuelve la ejecución activa actual si existe.")
async def get_status():
    """API-01: Estado de scraping consultado desde bot_ejecuciones (persistente)."""
    return obtener_estado_scraping()


@app.get("/api/logs", summary="Obtener Logs", description="Lee el archivo bot.log desde un byte offset específico para carga progresiva sin saturar memoria.")
async def get_logs(offset: int = 0):
    """API-03: Lee el archivo log usando seek al byte correspondiente (mejor rendimiento)."""
    log_file = "logs/bot.log"
    if not os.path.exists(log_file):
        return {"logs": [], "next_offset": 0}
        
    logs = []
    with open(log_file, "r", encoding="utf-8") as f:
        f.seek(offset)
        lines = f.readlines()
        next_offset = f.tell()
        
    return {"logs": lines, "next_offset": next_offset}


@app.post("/api/clear-logs", dependencies=[Depends(verify_api_key)])
async def clear_logs():
    """Limpia los logs de bot.log protegido por API Key (SEG-05)."""
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/bot.log", "w", encoding="utf-8") as f:
            f.write("")
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/api/data/{tipo}")
async def get_data(tipo: str):
    if tipo == "estudiantes":
        data = obtener_estudiantes(limit=500)
    elif tipo == "docentes":
        data = obtener_docentes(limit=500)
    else:
        data = []
    return {"data": data}


@app.get("/api/stats")
async def get_stats():
    """Devuelve conteos rápidos de estudiantes y docentes para el dashboard."""
    stats = {"estudiantes": 0, "docentes": 0, "error": None}
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM estudiantes;")
            stats["estudiantes"] = cursor.fetchone()[0]
        except Exception:
            pass
        try:
            cursor.execute("SELECT COUNT(*) FROM docentes;")
            stats["docentes"] = cursor.fetchone()[0]
        except Exception:
            pass
    except Exception as e:
        stats["error"] = str(e)
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)
    return stats


# =============================================================================
# Nuevos endpoints — Módulos de Importación
# =============================================================================

class ManualImportRequest(BaseModel):
    tipo: str = Field(..., description="Tipo de persona", example="estudiante")
    nombre: str = Field(..., description="Nombre completo", example="Juan Pérez")
    codigo_interno: Optional[str] = Field(None, description="Código de sistema interno", example="EST-12345")
    documento_nacional: Optional[str] = Field(None, description="Documento de identidad", example="1000000000")
    grado: Optional[str] = Field(None, description="Grado escolar", example="Primero")
    curso: Optional[str] = Field(None, description="Letra del grupo/curso", example="A")
    jornada: Optional[str] = Field(None, description="Jornada académica", example="Completa")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tipo": "estudiante",
                "nombre": "Juan Pérez",
                "codigo_interno": "EST-12345",
                "documento_nacional": "1000000000",
                "grado": "Primero",
                "curso": "A",
                "jornada": "Completa"
            }
        }
    }

    @field_validator('tipo', 'nombre', mode='before')
    @classmethod
    def check_required_fields(cls, v, info):
        if v is None or str(v).strip() == "":
            raise ValueError(f"El campo '{info.field_name}' no puede estar vacío.")
        return str(v).strip()

    @field_validator('codigo_interno', 'documento_nacional', 'grado', 'curso', 'jornada', mode='before')
    @classmethod
    def sanitize_optional_fields(cls, v):
        if v is not None:
            v = str(v).strip()
            return v if v else None
        return v


class BulkImportRequest(BaseModel):
    tipo: str = Field(..., description="Tipo de persona a importar en lote", example="estudiante")
    registros: List[Dict] = Field(..., description="Lista de diccionarios con datos de cada registro")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tipo": "estudiante",
                "registros": [
                    {"nombre": "Maria Gomez", "grado": "Segundo", "curso": "B"},
                    {"nombre": "Carlos Díaz", "grado": "Tercero"}
                ]
            }
        }
    }


class AddGroupRequest(BaseModel):
    grado: str = Field(..., description="Nombre del grado al cual añadir el grupo", example="Primero")
    grupo: str = Field(..., description="Nombre de la letra o grupo a crear", example="B")

    model_config = {
        "json_schema_extra": {
            "example": {
                "grado": "Primero",
                "grupo": "B"
            }
        }
    }

    @field_validator('grado', 'grupo', mode='before')
    @classmethod
    def check_not_empty(cls, v, info):
        if v is None or str(v).strip() == "":
            raise ValueError(f"El campo '{info.field_name}' no puede estar vacío.")
        return str(v).strip()


@app.post("/api/import/manual", dependencies=[Depends(verify_api_key)], summary="Importación Manual", description="Añade o actualiza un registro individual de estudiante o docente.")
async def import_manual(req: ManualImportRequest):
    """Guarda un registro individual protegido por API Key (SEG-05)."""
    if req.tipo not in ["estudiante", "docente"]:
        return JSONResponse({"status": "error", "message": "Tipo inválido"}, status_code=400)

    datos = {
        "nombre": req.nombre,
        "codigo_interno": req.codigo_interno,
        "documento_nacional": req.documento_nacional,
        "grado": req.grado,
        "curso": req.curso,
        "jornada": req.jornada,
    }
    result = insertar_o_actualizar_persona(req.tipo, datos)
    if result["status"] == "error":
        return JSONResponse(result, status_code=400)
    return result


@app.post("/api/import/bulk", dependencies=[Depends(verify_api_key)], summary="Importación Masiva", description="Procesa un lote de registros aplicando savepoints para asegurar que los registros válidos se guarden aunque algunos fallen.")
async def import_bulk(req: BulkImportRequest):
    """Procesa un lote masivo de registros de forma tolerante a fallos y protegido por API Key (SEG-05, COD-03)."""
    if req.tipo not in ["estudiante", "docente"]:
        return JSONResponse({"status": "error", "message": "Tipo inválido"}, status_code=400)

    if not req.registros:
        return JSONResponse({"status": "error", "message": "No hay registros para procesar."}, status_code=400)

    result = procesar_importacion_masiva(req.tipo, req.registros)
    return result


@app.get("/api/check-duplicate")
async def check_duplicate(tipo: str, codigo: str = "", documento: str = ""):
    """Verifica si un código/documento ya existe."""
    if tipo not in ["estudiante", "docente"]:
        return JSONResponse({"status": "error", "message": "Tipo inválido"}, status_code=400)

    record = verificar_duplicado(tipo, codigo or None, documento or None)
    return {"exists": record is not None, "record": record}


@app.get("/api/grupos")
async def get_grupos():
    """Retorna todos los grupos por grado."""
    grupos = obtener_grupos()
    return {"grupos": grupos}


@app.post("/api/grupos", dependencies=[Depends(verify_api_key)])
async def add_grupo(req: AddGroupRequest):
    """Añade un grupo a un grado protegido por API Key (SEG-05)."""
    if not req.grado:
        return JSONResponse({"status": "error", "message": "Debes seleccionar un grado antes de añadir un grupo."}, status_code=400)
    result = agregar_grupo(req.grado, req.grupo)
    if result["status"] == "error":
        return JSONResponse(result, status_code=500)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
