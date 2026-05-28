-- =============================================================================
-- sql/migrate_criticos_fase0.sql — Migración requerimientos críticos Fase 0
-- =============================================================================
-- Idempotente: puede ejecutarse múltiples veces sin errores.
-- Ejecutar sobre BD existente: psql -U postgres -d paz_y_salvo -f sql/migrate_criticos_fase0.sql
-- =============================================================================

-- 1. Crear tabla login (SEG-03)
CREATE TABLE IF NOT EXISTS login (
    id              SERIAL       PRIMARY KEY,
    url_plataforma  VARCHAR(255) NOT NULL,
    usuario         VARCHAR(100) NOT NULL,
    password_enc    TEXT         NOT NULL,
    tipo_usuario    VARCHAR(50)  NOT NULL DEFAULT 'Administrativo',
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Añadir columna tipo a bot_ejecuciones (SEG-06 prep / trazabilidad)
ALTER TABLE bot_ejecuciones ADD COLUMN IF NOT EXISTS tipo VARCHAR(20);

-- 3. Añadir columna login_id a bot_ejecuciones como FK nullable a login (SEG-06)
ALTER TABLE bot_ejecuciones ADD COLUMN IF NOT EXISTS login_id INT;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'bot_ejecuciones'
          AND constraint_name = 'fk_bot_ejecuciones_login'
    ) THEN
        ALTER TABLE bot_ejecuciones
            ADD CONSTRAINT fk_bot_ejecuciones_login
            FOREIGN KEY (login_id) REFERENCES login(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 4. Marcar ejecuciones huérfanas previas como 'interrumpido' (API-01)
UPDATE bot_ejecuciones
SET estado = 'interrumpido', fecha_fin = CURRENT_TIMESTAMP
WHERE fecha_fin IS NULL AND estado = 'iniciado';
