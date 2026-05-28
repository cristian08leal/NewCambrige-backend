-- sql/migrate_sprint2_indices.sql
-- Índices de rendimiento (BD-07). Idempotente: usa IF NOT EXISTS.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'estudiantes' AND indexname = 'idx_estudiantes_grado_curso'
    ) THEN
        CREATE INDEX idx_estudiantes_grado_curso ON estudiantes(grado_id, curso);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'asignaciones' AND indexname = 'idx_asignaciones_grado_perf'
    ) THEN
        CREATE INDEX idx_asignaciones_grado_perf ON asignaciones(grado_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'bot_ejecuciones' AND indexname = 'idx_ejecuciones_fecha_inicio'
    ) THEN
        CREATE INDEX idx_ejecuciones_fecha_inicio ON bot_ejecuciones(fecha_inicio DESC);
    END IF;
END $$;
