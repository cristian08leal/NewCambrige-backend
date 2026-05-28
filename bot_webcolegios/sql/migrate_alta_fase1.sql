-- =============================================================================
-- sql/migrate_alta_fase1.sql — Migración segura y normalización Fase 1
-- =============================================================================
-- Permite migrar la base de datos de Fase 0 a Fase 1 sin pérdida de datos.
-- =============================================================================

BEGIN;

-- 1. Crear tabla jornadas de catálogo
CREATE TABLE IF NOT EXISTS jornadas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insertar jornadas por defecto
INSERT INTO jornadas (nombre) VALUES 
    ('Completa'), 
    ('Continua'), 
    ('Nocturna')
ON CONFLICT (nombre) DO NOTHING;

-- 2. Asegurar que grados.nombre tenga restricción UNIQUE
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'grados' AND constraint_name = 'unique_grados_nombre'
    ) THEN
        ALTER TABLE grados ADD CONSTRAINT unique_grados_nombre UNIQUE (nombre);
    END IF;
END $$;

-- Resetear secuencia de grados para evitar conflictos con el ID 1 ya insertado
SELECT setval('grados_grado_id_seq', COALESCE((SELECT MAX(grado_id) FROM grados), 1) + 1, false);

-- Insertar los 15 grados estándar si no existen
INSERT INTO grados (nombre) VALUES
    ('Párvulos'), ('Prejardín'), ('Jardín'), ('Preescolar'),
    ('Primero'), ('Segundo'), ('Tercero'), ('Cuarto'), ('Quinto'),
    ('Sexto'), ('Séptimo'), ('Octavo'), ('Noveno'), ('Décimo'), ('Once')
ON CONFLICT (nombre) DO NOTHING;

-- 3. Normalizar grado_texto en estudiantes, docentes y grupos (limpieza de codificación/acentos)
UPDATE estudiantes SET grado_texto = 'Párvulos' WHERE grado_texto ILIKE '%arvulos%';
UPDATE estudiantes SET grado_texto = 'Prejardín' WHERE grado_texto ILIKE '%prejardin%' OR grado_texto ILIKE '%prejard%n%';
UPDATE estudiantes SET grado_texto = 'Jardín' WHERE (grado_texto ILIKE '%jardin%' OR grado_texto ILIKE '%jard%n%') AND NOT (grado_texto ILIKE '%pre%');
UPDATE estudiantes SET grado_texto = 'Preescolar' WHERE grado_texto ILIKE '%preescolar%' OR grado_texto ILIKE '%transici%';
UPDATE estudiantes SET grado_texto = 'Primero' WHERE grado_texto ILIKE '%primero%';
UPDATE estudiantes SET grado_texto = 'Segundo' WHERE grado_texto ILIKE '%segundo%';
UPDATE estudiantes SET grado_texto = 'Tercero' WHERE grado_texto ILIKE '%tercero%';
UPDATE estudiantes SET grado_texto = 'Cuarto' WHERE grado_texto ILIKE '%cuarto%';
UPDATE estudiantes SET grado_texto = 'Quinto' WHERE grado_texto ILIKE '%quinto%';
UPDATE estudiantes SET grado_texto = 'Sexto' WHERE grado_texto ILIKE '%sexto%';
UPDATE estudiantes SET grado_texto = 'Séptimo' WHERE grado_texto ILIKE '%septimo%' OR grado_texto ILIKE '%s%ptimo%';
UPDATE estudiantes SET grado_texto = 'Octavo' WHERE grado_texto ILIKE '%octavo%';
UPDATE estudiantes SET grado_texto = 'Noveno' WHERE grado_texto ILIKE '%noveno%';
UPDATE estudiantes SET grado_texto = 'Décimo' WHERE grado_texto ILIKE '%decimo%' OR grado_texto ILIKE '%d%cimo%';
UPDATE estudiantes SET grado_texto = 'Once' WHERE grado_texto ILIKE '%once%';

-- Normalizar docentes
UPDATE docentes SET grado_titular = 'Párvulos' WHERE grado_titular ILIKE '%arvulos%';
UPDATE docentes SET grado_titular = 'Prejardín' WHERE grado_titular ILIKE '%prejardin%' OR grado_titular ILIKE '%prejard%n%';
UPDATE docentes SET grado_titular = 'Jardín' WHERE (grado_titular ILIKE '%jardin%' OR grado_titular ILIKE '%jard%n%') AND NOT (grado_titular ILIKE '%pre%');
UPDATE docentes SET grado_titular = 'Preescolar' WHERE grado_titular ILIKE '%preescolar%' OR grado_titular ILIKE '%transici%';
UPDATE docentes SET grado_titular = 'Primero' WHERE grado_titular ILIKE '%primero%';
UPDATE docentes SET grado_titular = 'Segundo' WHERE grado_titular ILIKE '%segundo%';
UPDATE docentes SET grado_titular = 'Tercero' WHERE grado_titular ILIKE '%tercero%';
UPDATE docentes SET grado_titular = 'Cuarto' WHERE grado_titular ILIKE '%cuarto%';
UPDATE docentes SET grado_titular = 'Quinto' WHERE grado_titular ILIKE '%quinto%';
UPDATE docentes SET grado_titular = 'Sexto' WHERE grado_titular ILIKE '%sexto%';
UPDATE docentes SET grado_titular = 'Séptimo' WHERE grado_titular ILIKE '%septimo%' OR grado_titular ILIKE '%s%ptimo%';
UPDATE docentes SET grado_titular = 'Octavo' WHERE grado_titular ILIKE '%octavo%';
UPDATE docentes SET grado_titular = 'Noveno' WHERE grado_titular ILIKE '%noveno%';
UPDATE docentes SET grado_titular = 'Décimo' WHERE grado_titular ILIKE '%decimo%' OR grado_titular ILIKE '%d%cimo%';
UPDATE docentes SET grado_titular = 'Once' WHERE grado_titular ILIKE '%once%';

-- Normalizar grupos
UPDATE grupos SET grado = 'Párvulos' WHERE grado ILIKE '%arvulos%';
UPDATE grupos SET grado = 'Prejardín' WHERE grado ILIKE '%prejardin%' OR grado ILIKE '%prejard%n%';
UPDATE grupos SET grado = 'Jardín' WHERE (grado ILIKE '%jardin%' OR grado ILIKE '%jard%n%') AND NOT (grado ILIKE '%pre%');
UPDATE grupos SET grado = 'Preescolar' WHERE grado ILIKE '%preescolar%' OR grado ILIKE '%transici%';
UPDATE grupos SET grado = 'Primero' WHERE grado ILIKE '%primero%';
UPDATE grupos SET grado = 'Segundo' WHERE grado ILIKE '%segundo%';
UPDATE grupos SET grado = 'Tercero' WHERE grado ILIKE '%tercero%';
UPDATE grupos SET grado = 'Cuarto' WHERE grado ILIKE '%cuarto%';
UPDATE grupos SET grado = 'Quinto' WHERE grado ILIKE '%quinto%';
UPDATE grupos SET grado = 'Sexto' WHERE grado ILIKE '%sexto%';
UPDATE grupos SET grado = 'Séptimo' WHERE grado ILIKE '%septimo%' OR grado ILIKE '%s%ptimo%';
UPDATE grupos SET grado = 'Octavo' WHERE grado ILIKE '%octavo%';
UPDATE grupos SET grado = 'Noveno' WHERE grado ILIKE '%noveno%';
UPDATE grupos SET grado = 'Décimo' WHERE grado ILIKE '%decimo%' OR grado ILIKE '%d%cimo%';
UPDATE grupos SET grado = 'Once' WHERE grado ILIKE '%once%';

-- 4. Asociar e inicializar llaves foráneas en estudiantes
ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS jornada_id INT;

UPDATE estudiantes e
SET jornada_id = j.id
FROM jornadas j
WHERE UPPER(TRIM(e.jornada)) = UPPER(TRIM(j.nombre));

-- Mapear grado_id en estudiantes según grado_texto
UPDATE estudiantes e
SET grado_id = g.grado_id
FROM grados g
WHERE UPPER(TRIM(e.grado_texto)) = UPPER(TRIM(g.nombre));

-- Si queda alguna jornada sin asignar, poner por defecto la primera (Completa)
UPDATE estudiantes
SET jornada_id = (SELECT id FROM jornadas LIMIT 1)
WHERE jornada_id IS NULL;

ALTER TABLE estudiantes ALTER COLUMN jornada_id SET NOT NULL;

-- Agregar restricciones de FK a estudiantes si no existen
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'estudiantes' AND constraint_name = 'fk_jornada'
    ) THEN
        ALTER TABLE estudiantes
            ADD CONSTRAINT fk_jornada FOREIGN KEY (jornada_id) REFERENCES jornadas(id) ON DELETE RESTRICT;
    END IF;
END $$;

-- 5. Asociar e inicializar llaves foráneas en grupos
ALTER TABLE grupos ADD COLUMN IF NOT EXISTS grado_id INT;

UPDATE grupos gr
SET grado_id = g.grado_id
FROM grados g
WHERE UPPER(TRIM(gr.grado)) = UPPER(TRIM(g.nombre));

-- Poner default grado_id = 1 si no se mapeó
UPDATE grupos SET grado_id = 1 WHERE grado_id IS NULL;

ALTER TABLE grupos ALTER COLUMN grado_id SET NOT NULL;

-- Agregar restricción FK a grupos
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'grupos' AND constraint_name = 'fk_grado_grupo'
    ) THEN
        ALTER TABLE grupos
            ADD CONSTRAINT fk_grado_grupo FOREIGN KEY (grado_id) REFERENCES grados(grado_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Reemplazar la restricción única en grupos: UNIQUE(grado_id, grupo) en lugar de UNIQUE(grado, grupo)
ALTER TABLE grupos DROP CONSTRAINT IF EXISTS grupos_grado_grupo_key;
ALTER TABLE grupos DROP CONSTRAINT IF EXISTS unique_grado_id_grupo;
ALTER TABLE grupos ADD CONSTRAINT unique_grado_id_grupo UNIQUE (grado_id, grupo);

-- 6. Crear tabla de asignaciones para docentes titulares
CREATE TABLE IF NOT EXISTS asignaciones (
    id SERIAL PRIMARY KEY,
    docente_id INT NOT NULL,
    grado_id INT NOT NULL,
    curso VARCHAR(50) NOT NULL,
    vigente BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_docente FOREIGN KEY (docente_id) REFERENCES docentes(id) ON DELETE CASCADE,
    CONSTRAINT fk_grado FOREIGN KEY (grado_id) REFERENCES grados(grado_id) ON DELETE RESTRICT,
    CONSTRAINT unique_docente_grado_curso_vigente UNIQUE (docente_id, grado_id, curso, vigente)
);

-- Migrar datos de docentes a asignaciones
INSERT INTO asignaciones (docente_id, grado_id, curso, vigente)
SELECT d.id, g.grado_id, d.curso_titular, TRUE
FROM docentes d
JOIN grados g ON UPPER(TRIM(d.grado_titular)) = UPPER(TRIM(g.nombre))
WHERE d.grado_titular IS NOT NULL AND d.curso_titular IS NOT NULL
ON CONFLICT DO NOTHING;

-- 7. Eliminar triggers antiguos de sincronización desnormalizada
DROP TRIGGER IF EXISTS trg_sync_titular_estudiantes ON docentes;
DROP FUNCTION IF EXISTS fn_sync_titular_estudiantes();

-- 8. Eliminar columnas obsoletas desnormalizadas
ALTER TABLE estudiantes DROP COLUMN IF EXISTS jornada;
ALTER TABLE estudiantes DROP COLUMN IF EXISTS grado_texto;
ALTER TABLE estudiantes DROP COLUMN IF EXISTS titular;

ALTER TABLE grupos DROP COLUMN IF EXISTS grado;

ALTER TABLE docentes DROP COLUMN IF EXISTS grado_titular;
ALTER TABLE docentes DROP COLUMN IF EXISTS curso_titular;

COMMIT;
