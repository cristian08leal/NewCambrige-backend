// =============================================================================
// utils/templateGenerator.js — Genera plantillas Excel descargables
// =============================================================================
import * as XLSX from 'xlsx'

const STUDENT_COLUMNS = [
  'Nombre y apellidos',
  'Código interno',
  'Documento nacional',
  'Grado',
  'Curso/Grupo',
  'Jornada'
]

const TEACHER_COLUMNS = [
  'Nombre y apellidos',
  'Código interno',
  'Documento nacional',
  'Grado asignado',
  'Grupo asignado'
]

const STUDENT_INSTRUCTIONS = [
  {
    Campo: 'Nombre y apellidos',
    Descripcion: 'Nombre completo del estudiante',
    Obligatorio: 'Sí',
    'Valores válidos': 'Texto libre',
    Ejemplo: 'García López Juan Carlos'
  },
  {
    Campo: 'Código interno',
    Descripcion: 'Código asignado por el colegio. Si no se tiene, se puede dejar vacío si se proporciona el documento nacional.',
    Obligatorio: 'Condicional',
    'Valores válidos': 'Texto/Número',
    Ejemplo: 'EST-2024-001'
  },
  {
    Campo: 'Documento nacional',
    Descripcion: 'Cédula, TI, RC u otro documento de identificación. Si no se tiene, se puede dejar vacío si se proporciona el código interno.',
    Obligatorio: 'Condicional',
    'Valores válidos': 'Texto/Número',
    Ejemplo: '1001234567'
  },
  {
    Campo: 'Grado',
    Descripcion: 'Grado escolar del estudiante',
    Obligatorio: 'Sí',
    'Valores válidos': 'Párvulos, Prejardín, Jardín, Preescolar, Primero, Segundo, Tercero, Cuarto, Quinto, Sexto, Séptimo, Octavo, Noveno, Décimo, Once',
    Ejemplo: 'Quinto'
  },
  {
    Campo: 'Curso/Grupo',
    Descripcion: 'Grupo o salón asignado',
    Obligatorio: 'Sí',
    'Valores válidos': 'A, B, C, D... (según grupos disponibles)',
    Ejemplo: 'A'
  },
  {
    Campo: 'Jornada',
    Descripcion: 'Jornada escolar',
    Obligatorio: 'Sí',
    'Valores válidos': 'Completa, Continua, Nocturna',
    Ejemplo: 'Completa'
  }
]

const TEACHER_INSTRUCTIONS = [
  {
    Campo: 'Nombre y apellidos',
    Descripcion: 'Nombre completo del docente',
    Obligatorio: 'Sí',
    'Valores válidos': 'Texto libre',
    Ejemplo: 'Martínez Rojas Pedro'
  },
  {
    Campo: 'Código interno',
    Descripcion: 'Código asignado por el colegio. Si no se tiene, se puede dejar vacío si se proporciona el documento nacional.',
    Obligatorio: 'Condicional',
    'Valores válidos': 'Texto/Número',
    Ejemplo: 'DOC-2024-010'
  },
  {
    Campo: 'Documento nacional',
    Descripcion: 'Cédula u otro documento de identificación. Si no se tiene, se puede dejar vacío si se proporciona el código interno.',
    Obligatorio: 'Condicional',
    'Valores válidos': 'Texto/Número',
    Ejemplo: '60267973'
  },
  {
    Campo: 'Grado asignado',
    Descripcion: 'Grado donde el docente es titular. Si no aplica, dejar vacío.',
    Obligatorio: 'No',
    'Valores válidos': 'Párvulos, Prejardín, Jardín, Preescolar, Primero, Segundo, Tercero, Cuarto, Quinto, Sexto, Séptimo, Octavo, Noveno, Décimo, Once',
    Ejemplo: 'Tercero'
  },
  {
    Campo: 'Grupo asignado',
    Descripcion: 'Grupo donde el docente es titular. Si no aplica, dejar vacío.',
    Obligatorio: 'No',
    'Valores válidos': 'A, B, C, D...',
    Ejemplo: 'A'
  }
]

/**
 * Genera y descarga una plantilla Excel.
 * @param {'estudiante'|'docente'} tipo
 */
export function downloadTemplate(tipo) {
  const wb = XLSX.utils.book_new()

  // Hoja 1 — Datos
  const columns = tipo === 'estudiante' ? STUDENT_COLUMNS : TEACHER_COLUMNS
  const dataSheet = XLSX.utils.aoa_to_sheet([columns])

  // Ajustar ancho de columnas
  dataSheet['!cols'] = columns.map(() => ({ wch: 22 }))
  XLSX.utils.book_append_sheet(wb, dataSheet, 'Datos')

  // Hoja 2 — Instrucciones
  const instructions = tipo === 'estudiante' ? STUDENT_INSTRUCTIONS : TEACHER_INSTRUCTIONS
  const instrSheet = XLSX.utils.json_to_sheet(instructions)
  instrSheet['!cols'] = [
    { wch: 22 }, { wch: 50 }, { wch: 14 }, { wch: 50 }, { wch: 22 }
  ]
  XLSX.utils.book_append_sheet(wb, instrSheet, 'Instrucciones')

  const filename = tipo === 'estudiante'
    ? 'plantilla_estudiantes.xlsx'
    : 'plantilla_docentes.xlsx'

  XLSX.writeFile(wb, filename)
}
