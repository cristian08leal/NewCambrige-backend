from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class StagingEstudiante(Base):
    __tablename__ = "staging_estudiantes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    documento = Column(String(30), nullable=False)
    codigo_interno = Column(String(50))
    curso = Column(String(50))
    jornada = Column(String(50))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class StagingDocente(Base):
    __tablename__ = "staging_docentes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    documento = Column(String(30), nullable=False)
    codigo_interno = Column(String(50))
    curso = Column(String(50))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class SyncEjecucion(Base):
    __tablename__ = "sync_ejecuciones"
    id = Column(Integer, primary_key=True, index=True)
    fase = Column(Integer, nullable=False) # 1: Estudiantes, 2: Docentes, 3: Paz y Salvos
    estado = Column(String(20), nullable=False) # 'EN_PROGRESO', 'COMPLETADO', 'ERROR'
    registros_procesados = Column(Integer, default=0)
    detalles = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
