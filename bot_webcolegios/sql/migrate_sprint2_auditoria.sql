-- sql/migrate_sprint2_auditoria.sql
-- Auditoría con updated_at (BD-08). Idempotente.

-- 1. Agregar updated_at a estudiantes
ALTER TABLE estudiantes
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 2. Agregar updated_at a docentes
ALTER TABLE docentes
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 3. Función genérica de actualización automática
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Trigger en estudiantes (idempotente)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_estudiantes_updated_at'
    ) THEN
        CREATE TRIGGER trg_estudiantes_updated_at
        BEFORE UPDATE ON estudiantes
        FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
    END IF;
END $$;

-- 5. Trigger en docentes (idempotente)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_docentes_updated_at'
    ) THEN
        CREATE TRIGGER trg_docentes_updated_at
        BEFORE UPDATE ON docentes
        FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
    END IF;
END $$;
