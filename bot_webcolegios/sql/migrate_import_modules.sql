-- =============================================================================
-- sql/migrate_import_modules.sql — Migración para módulos de importación
-- =============================================================================
-- Ejecutar UNA VEZ sobre una BD existente que ya tenga las tablas originales.
-- Es idempotente: puede ejecutarse múltiples veces sin errores.
-- =============================================================================

-- 1. Añadir codigo_interno a estudiantes
ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS codigo_interno VARCHAR(100);
CREATE UNIQUE INDEX IF NOT EXISTS idx_codigo_interno_est
    ON estudiantes(codigo_interno) WHERE codigo_interno IS NOT NULL;

-- 2. Añadir codigo_interno a docentes
ALTER TABLE docentes ADD COLUMN IF NOT EXISTS codigo_interno VARCHAR(100);
CREATE UNIQUE INDEX IF NOT EXISTS idx_codigo_interno_doc
    ON docentes(codigo_interno) WHERE codigo_interno IS NOT NULL;

-- 3. Crear tabla de grupos dinámicos
CREATE TABLE IF NOT EXISTS grupos (
    id          SERIAL      PRIMARY KEY,
    grado       VARCHAR(50) NOT NULL,
    grupo       VARCHAR(10) NOT NULL,
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(grado, grupo)
);

-- 4. Insertar grupo "A" por defecto para cada grado
INSERT INTO grupos (grado, grupo) VALUES
    ('Párvulos', 'A'), ('Prejardín', 'A'), ('Jardín', 'A'), ('Preescolar', 'A'),
    ('Primero', 'A'), ('Segundo', 'A'), ('Tercero', 'A'), ('Cuarto', 'A'), ('Quinto', 'A'),
    ('Sexto', 'A'), ('Séptimo', 'A'), ('Octavo', 'A'), ('Noveno', 'A'), ('Décimo', 'A'), ('Once', 'A')
ON CONFLICT (grado, grupo) DO NOTHING;
