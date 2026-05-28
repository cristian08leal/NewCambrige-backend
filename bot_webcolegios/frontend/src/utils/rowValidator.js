// =============================================================================
// utils/rowValidator.js — Validación de filas según tipo de persona
// =============================================================================

const GRADOS_VALIDOS = [
  'Párvulos', 'Prejardín', 'Jardín', 'Preescolar',
  'Primero', 'Segundo', 'Tercero', 'Cuarto', 'Quinto',
  'Sexto', 'Séptimo', 'Octavo', 'Noveno', 'Décimo', 'Once'
]

const JORNADAS_VALIDAS = ['Completa', 'Continua', 'Nocturna']

/**
 * Valida una fila individual según el tipo de persona.
 * @param {Object} row - Fila con campos del sistema (ya mapeada)
 * @param {string} tipo - "estudiante" o "docente"
 * @returns {{ valid: boolean, reason: string|null }}
 */
export function validateRow(row, tipo) {
  const nombre = (row.nombre || '').trim()
  const codigo = (row.codigo_interno || '').trim()
  const documento = (row.documento_nacional || '').trim()

  if (!nombre) {
    return { valid: false, reason: 'nombre vacío' }
  }

  if (!codigo && !documento) {
    return { valid: false, reason: 'falta documento y código interno' }
  }

  if (tipo === 'estudiante') {
    const grado = (row.grado || '').trim()
    const curso = (row.curso || '').trim()
    const jornada = (row.jornada || '').trim()

    if (!grado) {
      return { valid: false, reason: 'grado vacío' }
    }
    if (!GRADOS_VALIDOS.includes(grado)) {
      return { valid: false, reason: `grado "${grado}" no reconocido` }
    }
    if (!curso) {
      return { valid: false, reason: 'curso/grupo vacío' }
    }
    if (!jornada) {
      return { valid: false, reason: 'jornada vacía' }
    }
    if (!JORNADAS_VALIDAS.includes(jornada)) {
      return { valid: false, reason: `jornada "${jornada}" no reconocida` }
    }
  }

  return { valid: true, reason: null }
}

/**
 * Valida los campos del formulario manual en tiempo real.
 * Retorna un objeto con errores por campo.
 * @param {Object} fields - { nombre, codigo_interno, documento_nacional, grado, curso, jornada }
 * @param {string} tipo - "estudiante" o "docente"
 * @returns {Object} errores - { campo: "mensaje de error" }
 */
export function validateManualFields(fields, tipo) {
  const errors = {}

  // Identificadores
  const codigo = (fields.codigo_interno || '').trim()
  const documento = (fields.documento_nacional || '').trim()
  if (!codigo && !documento) {
    errors._identificadores = 'Debes ingresar al menos el código interno o el documento nacional.'
  }

  if (tipo === 'estudiante') {
    if (!fields.grado) {
      errors.grado = 'El grado es obligatorio.'
    }
    if (!fields.curso) {
      errors.curso = 'El curso/grupo es obligatorio.'
    }
    if (!fields.jornada) {
      errors.jornada = 'La jornada es obligatoria.'
    }
  }

  return errors
}

export { GRADOS_VALIDOS, JORNADAS_VALIDAS }
