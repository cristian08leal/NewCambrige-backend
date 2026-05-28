from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SyncResponse(BaseModel):
    mensaje: str
    ejecucion_id: int
    estado: str

class EjecucionDetalle(BaseModel):
    id: int
    fase: int
    estado: str
    registros_procesados: int
    detalles: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
