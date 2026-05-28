from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from . import schemas, service

router = APIRouter(prefix="/webcolegios", tags=["Sincronización WebColegios"])

@router.post("/sincronizar", response_model=schemas.SyncResponse)
def iniciar_sincronizacion(background_tasks: BackgroundTasks, fase: int = 1, db: Session = Depends(get_db)):
    """
    Inicia el proceso de sincronización con WebColegios.
    fase 1 = Estudiantes, fase 2 = Docentes.
    El proceso es largo, por lo que se ejecuta en segundo plano.
    """
    if fase not in [1, 2]:
        raise HTTPException(status_code=400, detail="Fase no válida. Use 1 (Estudiantes) o 2 (Docentes).")
        
    ejecucion_id = service.registrar_inicio_ejecucion(db, fase)
    
    background_tasks.add_task(service.ejecutar_scraping_background, db_session=db, ejecucion_id=ejecucion_id, fase=fase)
    
    return schemas.SyncResponse(
        mensaje=f"Sincronización fase {fase} iniciada en segundo plano.",
        ejecucion_id=ejecucion_id,
        estado="EN_PROGRESO"
    )

@router.get("/estado/{ejecucion_id}", response_model=schemas.EjecucionDetalle)
def consultar_estado(ejecucion_id: int, db: Session = Depends(get_db)):
    """
    Consulta el estado de una sincronización específica.
    """
    ejecucion = service.obtener_ejecucion(db, ejecucion_id)
    if not ejecucion:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada.")
    return ejecucion
