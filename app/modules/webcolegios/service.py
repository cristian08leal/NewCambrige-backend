from sqlalchemy.orm import Session
from .models import SyncEjecucion
from app.core.logger import logger

def registrar_inicio_ejecucion(db: Session, fase: int) -> int:
    ejec = SyncEjecucion(fase=fase, estado="EN_PROGRESO")
    db.add(ejec)
    db.commit()
    db.refresh(ejec)
    return ejec.id

def obtener_ejecucion(db: Session, ejecucion_id: int):
    return db.query(SyncEjecucion).filter(SyncEjecucion.id == ejecucion_id).first()

def ejecutar_scraping_background(db_session: Session, ejecucion_id: int, fase: int):
    try:
        if fase == 1:
            from .scraper.extraccion import extraccion_fase1
            extraccion_fase1()
        elif fase == 2:
            from .scraper.extraccion import extraccion_fase2
            extraccion_fase2()
            
        ejec = db_session.query(SyncEjecucion).filter(SyncEjecucion.id == ejecucion_id).first()
        if ejec:
            ejec.estado = "COMPLETADO"
            db_session.commit()
    except Exception as e:
        logger.error(f"Error en ejecución scraping background: {e}")
        ejec = db_session.query(SyncEjecucion).filter(SyncEjecucion.id == ejecucion_id).first()
        if ejec:
            ejec.estado = "ERROR"
            ejec.detalles = str(e)
            db_session.commit()
