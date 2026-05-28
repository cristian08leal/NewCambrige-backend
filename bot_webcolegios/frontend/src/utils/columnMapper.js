// =============================================================================
// utils/columnMapper.js — Mapeo flexible de columnas del archivo a campos del sistema
// =============================================================================

/**
 * Diccionario de sinónimos: cada campo del sistema mapea a múltiples posibles
 * nombres de columna del archivo.
 */
const SYNONYMS = {
  nombre: [
    'nombre', 'nombres', 'nombre completo', 'nombre y apellidos',
    'nombre y apellido', 'nombres y apellidos', 'alumno', 'estudiante',
    'docente', 'profesor', 'full name', 'name', 'apellidos y nombres',
    'nombre_completo', 'nombre apellido'
  ],
  codigo_interno: [
    'codigo interno', 'código interno', 'cod', 'codigo', 'código',
    'id interno', 'cod interno', 'code', 'internal code', 'id_interno',
    'codigo_interno', 'cod_interno'
  ],
  documento_nacional: [
    'documento', 'documento nacional', 'doc', 'cc', 'cédula', 'cedula',
    'ti', 'tarjeta de identidad', 'rc', 'registro civil', 'nit',
    'identificación', 'identificacion', 'num documento', 'número documento',
    'numero documento', 'document', 'documento_nacional', 'num_documento',
    'no. documento', 'no documento'
  ],
  grado: [
    'grado', 'grado_texto', 'nivel', 'grado asignado', 'grado_asignado',
    'grade', 'level', 'curso_nivel'
  ],
  curso: [
    'curso', 'grupo', 'salón', 'salon', 'curso/grupo', 'curso grupo',
    'grupo asignado', 'grupo_asignado', 'section', 'class', 'curso_grupo',
    'seccion', 'sección'
  ],
  jornada: [
    'jornada', 'turno', 'horario', 'shift', 'jornada_escolar'
  ]
}

/**
 * Normaliza un string para comparación: minúsculas, sin acentos, trim.
 */
function normalize(str) {
  return (str || '')
    .toString()
    .toLowerCase()
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[_\-\.]/g, ' ')
    .replace(/\s+/g, ' ')
}

/**
 * Intenta mapear las columnas del archivo a los campos esperados del sistema.
 * 
 * @param {string[]} fileColumns - Nombres de columnas del archivo
 * @param {string} tipo - "estudiante" o "docente"
 * @returns {{
 *   mapping: Object<string, string|null>,
 *   unmapped: string[],
 *   reverseMapping: Object<string, string>
 * }}
 */
export function mapColumns(fileColumns, tipo) {
  const fieldsNeeded = tipo === 'estudiante'
    ? ['nombre', 'codigo_interno', 'documento_nacional', 'grado', 'curso', 'jornada']
    : ['nombre', 'codigo_interno', 'documento_nacional', 'grado', 'curso']

  // mapping: campo del sistema → columna del archivo
  const mapping = {}
  const reverseMapping = {} // columna del archivo → campo del sistema
  const usedColumns = new Set()

  for (const field of fieldsNeeded) {
    mapping[field] = null
    const synonyms = SYNONYMS[field] || []
    const normalizedSynonyms = synonyms.map(normalize)

    for (const col of fileColumns) {
      if (usedColumns.has(col)) continue
      const normalizedCol = normalize(col)

      // Coincidencia exacta
      if (normalizedSynonyms.includes(normalizedCol)) {
        mapping[field] = col
        reverseMapping[col] = field
        usedColumns.add(col)
        break
      }
    }

    // Si no se encontró exacta, intentar coincidencia parcial
    if (!mapping[field]) {
      for (const col of fileColumns) {
        if (usedColumns.has(col)) continue
        const normalizedCol = normalize(col)

        for (const syn of normalizedSynonyms) {
          if (normalizedCol.includes(syn) || syn.includes(normalizedCol)) {
            mapping[field] = col
            reverseMapping[col] = field
            usedColumns.add(col)
            break
          }
        }
        if (mapping[field]) break
      }
    }
  }

  // Detectar campos obligatorios no mapeados
  const requiredFields = tipo === 'estudiante'
    ? ['nombre', 'grado', 'curso', 'jornada']
    : ['nombre']
  
  const unmapped = requiredFields.filter(f => !mapping[f])

  return { mapping, unmapped, reverseMapping }
}

/**
 * Aplica el mapeo a una fila del archivo, retornando un objeto con los campos del sistema.
 */
export function applyMapping(row, mapping) {
  const result = {}
  for (const [systemField, fileColumn] of Object.entries(mapping)) {
    if (fileColumn && row[fileColumn] !== undefined) {
      result[systemField] = String(row[fileColumn]).trim()
    } else {
      result[systemField] = ''
    }
  }
  return result
}

/**
 * Labels legibles para cada campo del sistema
 */
export const FIELD_LABELS = {
  nombre: 'Nombre y apellidos',
  codigo_interno: 'Código interno',
  documento_nacional: 'Documento nacional',
  grado: 'Grado',
  curso: 'Curso/Grupo',
  jornada: 'Jornada'
}
