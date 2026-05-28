// =============================================================================
// utils/fileParser.js — Parseo de archivos CSV, XLSX, XLS, JSON
// =============================================================================
import * as XLSX from 'xlsx'

const VALID_EXTENSIONS = ['.csv', '.xlsx', '.xls', '.json']

/**
 * Valida la extensión del archivo.
 * @returns {string|null} extensión válida o null
 */
export function getFileExtension(filename) {
  const ext = '.' + filename.split('.').pop().toLowerCase()
  return VALID_EXTENSIONS.includes(ext) ? ext : null
}

/**
 * Parsea un archivo y retorna un array de objetos [{col: val, ...}, ...]
 * @param {File} file
 * @returns {Promise<{data: Array, columns: string[], error: string|null}>}
 */
export async function parseFile(file) {
  const ext = getFileExtension(file.name)

  if (!ext) {
    return {
      data: [],
      columns: [],
      error: 'Formato no válido. Solo se aceptan archivos CSV, Excel o JSON.'
    }
  }

  try {
    if (ext === '.json') {
      return await parseJSON(file)
    } else {
      return await parseExcelOrCSV(file)
    }
  } catch (e) {
    return {
      data: [],
      columns: [],
      error: `Error al leer el archivo: ${e.message}`
    }
  }
}

async function parseJSON(file) {
  const text = await file.text()
  const parsed = JSON.parse(text)
  const arr = Array.isArray(parsed) ? parsed : [parsed]
  if (arr.length === 0) {
    return { data: [], columns: [], error: 'El archivo JSON está vacío.' }
  }
  const columns = Object.keys(arr[0])
  return { data: arr, columns, error: null }
}

async function parseExcelOrCSV(file) {
  const buffer = await file.arrayBuffer()
  const workbook = XLSX.read(buffer, { type: 'array', cellDates: true })

  // Usar la primera hoja
  const sheetName = workbook.SheetNames[0]
  const sheet = workbook.Sheets[sheetName]

  const data = XLSX.utils.sheet_to_json(sheet, { defval: '' })

  if (data.length === 0) {
    return { data: [], columns: [], error: 'El archivo está vacío o no tiene datos.' }
  }

  const columns = Object.keys(data[0])
  return { data, columns, error: null }
}
