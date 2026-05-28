// =============================================================================
// components/ImportContext.jsx — Estado compartido para módulos de importación
// =============================================================================
import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const ImportContext = createContext()

export const GRADOS = [
  'Párvulos', 'Prejardín', 'Jardín', 'Preescolar',
  'Primero', 'Segundo', 'Tercero', 'Cuarto', 'Quinto',
  'Sexto', 'Séptimo', 'Octavo', 'Noveno', 'Décimo', 'Once'
]

export const JORNADAS = ['Completa', 'Continua', 'Nocturna']

const LETRAS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

export function ImportProvider({ children }) {
  const [personType, setPersonType] = useState('estudiante')
  const [gruposPorGrado, setGruposPorGrado] = useState({})
  const [gruposLoaded, setGruposLoaded] = useState(false)

  // Cargar grupos desde la BD al montar
  const loadGrupos = useCallback(async () => {
    try {
      const res = await fetch('/api/grupos')
      const data = await res.json()
      if (data.grupos) {
        setGruposPorGrado(data.grupos)
      }
    } catch (e) {
      // Fallback: inicializar con A para cada grado
      const defaults = {}
      GRADOS.forEach(g => { defaults[g] = ['A'] })
      setGruposPorGrado(defaults)
    }
    setGruposLoaded(true)
  }, [])

  useEffect(() => { loadGrupos() }, [loadGrupos])

  // Obtener grupos para un grado
  const getGrupos = useCallback((grado) => {
    return gruposPorGrado[grado] || ['A']
  }, [gruposPorGrado])

  // Añadir siguiente grupo secuencial a un grado
  const addGrupo = useCallback(async (grado) => {
    if (!grado) return { ok: false, message: 'Debes seleccionar un grado antes de añadir un grupo.' }

    const current = gruposPorGrado[grado] || ['A']
    const lastLetter = current[current.length - 1]
    const nextIndex = LETRAS.indexOf(lastLetter) + 1

    if (nextIndex >= LETRAS.length) {
      return { ok: false, message: 'No se pueden añadir más grupos.' }
    }

    const nextLetter = LETRAS[nextIndex]

    try {
      const res = await fetch('/api/grupos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': 'dev-secret-key-12345' },
        body: JSON.stringify({ grado, grupo: nextLetter })
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setGruposPorGrado(prev => ({
          ...prev,
          [grado]: [...(prev[grado] || ['A']), nextLetter]
        }))
        return { ok: true, message: data.message, grupo: nextLetter }
      }
      return { ok: false, message: data.message }
    } catch (e) {
      return { ok: false, message: 'Error de conexión al añadir grupo.' }
    }
  }, [gruposPorGrado])

  return (
    <ImportContext.Provider value={{
      personType, setPersonType,
      gruposPorGrado, getGrupos, addGrupo,
      gruposLoaded, loadGrupos
    }}>
      {children}
    </ImportContext.Provider>
  )
}

export function useImport() {
  return useContext(ImportContext)
}
