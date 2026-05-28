-- =============================================================================
-- sql/migrate_staging_tables.sql — Tablas de transición (Staging Tables)
-- =============================================================================

-- Tabla de staging para carga masiva de estudiantes
CREATE TABLE IF NOT EXISTS staging_estudiantes (
    documento      VARCHAR(100) NULL,
    codigo_interno VARCHAR(100) NULL,
    nombre         VARCHAR(150) NULL,
    grado          VARCHAR(50)  NULL,
    curso          VARCHAR(50)  NULL,
    jornada        VARCHAR(50)  NULL
);

-- Tabla de staging para carga masiva de docentes
CREATE TABLE IF NOT EXISTS staging_docentes (
    documento      VARCHAR(100) NULL,
    codigo_interno VARCHAR(100) NULL,
    nombre         VARCHAR(150) NULL,
    grado_titular  VARCHAR(50)  NULL,
    curso_titular  VARCHAR(50)  NULL
);

-- Índices ligeros para optimizar los cruces de fusión (UPSERT)
CREATE INDEX IF NOT EXISTS idx_staging_est_doc ON staging_estudiantes(documento);
CREATE INDEX IF NOT EXISTS idx_staging_est_cod ON staging_estudiantes(codigo_interno);
CREATE INDEX IF NOT EXISTS idx_staging_doc_doc ON staging_docentes(documento);
