// =============================================================================
// components/ManualImport.jsx — Formulario de importación manual individual
// =============================================================================
import { useState, useEffect, useCallback } from 'react'
import {
  MdSave, MdAdd, MdCheckCircle, MdWarning, MdClose,
  MdList, MdError, MdEditNote
} from 'react-icons/md'
import { useImport, GRADOS, JORNADAS } from './ImportContext'
import { validateManualFields } from '../utils/rowValidator'

const INITIAL_FIELDS = {
  nombre: '',
  codigo_interno: '',
  documento_nacional: '',
  grado: '',
  curso: '',
  jornada: ''
}

export default function ManualImport({ onGoToList }) {
  const { personType, getGrupos, addGrupo } = useImport()

  const [fields, setFields] = useState({ ...INITIAL_FIELDS })
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})
  const [saving, setSaving] = useState(false)
  const [savedMsg, setSavedMsg] = useState(null)
  const [duplicateModal, setDuplicateModal] = useState(null)
  const [addGroupMsg, setAddGroupMsg] = useState(null)

  // Reset form when person type changes
  useEffect(() => {
    setFields({ ...INITIAL_FIELDS })
    setErrors({})
    setTouched({})
    setSavedMsg(null)
    setDuplicateModal(null)
  }, [personType])

  // Validate in real-time
  useEffect(() => {
    if (Object.keys(touched).length > 0) {
      const newErrors = validateManualFields(fields, personType)
      // Only show field-level errors for touched fields
      const visibleErrors = {}
      for (const [key, msg] of Object.entries(newErrors)) {
        if (key === '_identificadores') {
          // Always show if both identifiers have been touched
          if (touched.codigo_interno || touched.documento_nacional) {
            visibleErrors[key] = msg
          }
        } else if (touched[key]) {
          visibleErrors[key] = msg
        }
      }
      setErrors(visibleErrors)
    }
  }, [fields, personType, touched])

  const handleChange = (field, value) => {
    setFields(prev => ({ ...prev, [field]: value }))
    setTouched(prev => ({ ...prev, [field]: true }))
    setSavedMsg(null)
  }

  const handleBlur = (field) => {
    setTouched(prev => ({ ...prev, [field]: true }))
  }

  const handleAddGroup = async () => {
    if (!fields.grado) {
      setAddGroupMsg({ type: 'error', text: 'Debes seleccionar un grado antes de añadir un grupo.' })
      setTimeout(() => setAddGroupMsg(null), 3000)
      return
    }
    const result = await addGrupo(fields.grado)
    if (result.ok) {
      setAddGroupMsg({ type: 'ok', text: result.message })
    } else {
      setAddGroupMsg({ type: 'error', text: result.message })
    }
    setTimeout(() => setAddGroupMsg(null), 3000)
  }

  const handleSave = async () => {
    // Touch all fields to show all errors
    const allTouched = {}
    Object.keys(INITIAL_FIELDS).forEach(k => { allTouched[k] = true })
    setTouched(allTouched)

    // Validate
    const newErrors = validateManualFields(fields, personType)
    if (!fields.nombre.trim()) {
      newErrors.nombre = 'El nombre es obligatorio.'
    }
    setErrors(newErrors)
    if (Object.keys(newErrors).length > 0) return

    // Check for duplicates first
    const params = new URLSearchParams({
      tipo: personType,
      codigo: fields.codigo_interno,
      documento: fields.documento_nacional
    })
    try {
      const dupRes = await fetch(`/api/check-duplicate?${params}`)
      const dupData = await dupRes.json()
      if (dupData.exists) {
        setDuplicateModal(dupData.record)
        return
      }
    } catch { /* proceed to save */ }

    await doSave()
  }

  const doSave = async () => {
    setSaving(true)
    setDuplicateModal(null)
    try {
      const res = await fetch('/api/import/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': 'dev-secret-key-12345' },
        body: JSON.stringify({
          tipo: personType,
          nombre: fields.nombre,
          codigo_interno: fields.codigo_interno || null,
          documento_nacional: fields.documento_nacional || null,
          grado: fields.grado || null,
          curso: fields.curso || null,
          jornada: fields.jornada || null,
        })
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setSavedMsg({ type: 'ok', text: data.message })
      } else {
        setSavedMsg({ type: 'error', text: data.message })
      }
    } catch {
      setSavedMsg({ type: 'error', text: 'Error de conexión con el servidor.' })
    }
    setSaving(false)
  }

  const handleAddAnother = () => {
    setFields({ ...INITIAL_FIELDS })
    setErrors({})
    setTouched({})
    setSavedMsg(null)
  }

  const grupos = fields.grado ? getGrupos(fields.grado) : ['A']

  return (
    <div style={S.container}>
      <h3 style={S.title}>
        <MdEditNote size={20} style={{ marginRight: 6, verticalAlign: 'middle', marginTop: -2 }} />
        {personType === 'estudiante' ? 'Registro de Estudiante' : 'Registro de Docente'}
      </h3>

      {/* Nombre */}
      <div style={S.fieldGroup}>
        <label style={S.label}>Nombre y apellidos *</label>
        <input
          style={{ ...S.input, ...(errors.nombre ? S.inputError : {}) }}
          type="text"
          placeholder="Ej: García López Juan Carlos"
          value={fields.nombre}
          onChange={e => handleChange('nombre', e.target.value)}
          onBlur={() => handleBlur('nombre')}
        />
        {touched.nombre && errors.nombre && <span style={S.errorMsg}>{errors.nombre}</span>}
      </div>

      {/* Identificadores */}
      <div style={S.row2}>
        <div style={S.fieldGroup}>
          <label style={S.label}>Código interno</label>
          <input
            style={{ ...S.input, ...(errors._identificadores ? S.inputWarn : {}) }}
            type="text"
            placeholder="Ej: EST-2024-001"
            value={fields.codigo_interno}
            onChange={e => handleChange('codigo_interno', e.target.value)}
            onBlur={() => handleBlur('codigo_interno')}
          />
        </div>
        <div style={S.fieldGroup}>
          <label style={S.label}>Documento nacional</label>
          <input
            style={{ ...S.input, ...(errors._identificadores ? S.inputWarn : {}) }}
            type="text"
            placeholder="Ej: 1001234567"
            value={fields.documento_nacional}
            onChange={e => handleChange('documento_nacional', e.target.value)}
            onBlur={() => handleBlur('documento_nacional')}
          />
        </div>
      </div>
      {errors._identificadores && (
        <div style={S.idWarning}>
          <MdWarning size={13} /> {errors._identificadores}
        </div>
      )}

      {/* Grado y Curso */}
      <div style={S.row2}>
        <div style={S.fieldGroup}>
          <label style={S.label}>
            {personType === 'estudiante' ? 'Grado *' : 'Grado asignado'}
          </label>
          <select
            style={{ ...S.select, ...(errors.grado ? S.inputError : {}) }}
            value={fields.grado}
            onChange={e => {
              handleChange('grado', e.target.value)
              handleChange('curso', '') // reset curso al cambiar grado
            }}
          >
            <option value="">Seleccionar grado</option>
            {GRADOS.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
          {touched.grado && errors.grado && <span style={S.errorMsg}>{errors.grado}</span>}
        </div>

        <div style={S.fieldGroup}>
          <label style={S.label}>
            {personType === 'estudiante' ? 'Curso/Grupo *' : 'Grupo asignado'}
          </label>
          <div style={S.selectRow}>
            <select
              style={{ ...S.select, flex: 1, ...(errors.curso ? S.inputError : {}) }}
              value={fields.curso}
              onChange={e => handleChange('curso', e.target.value)}
            >
              <option value="">Seleccionar</option>
              {grupos.map(g => <option key={g} value={g}>{g}</option>)}
            </select>
            <button
              style={S.addGroupBtn}
              onClick={handleAddGroup}
              title="Añadir grupo"
              type="button"
            >
              <MdAdd size={14} />
            </button>
          </div>
          {touched.curso && errors.curso && <span style={S.errorMsg}>{errors.curso}</span>}
          {addGroupMsg && (
            <span style={{
              ...S.errorMsg,
              color: addGroupMsg.type === 'ok' ? 'var(--green)' : 'var(--red)'
            }}>
              {addGroupMsg.text}
            </span>
          )}
        </div>
      </div>

      {/* Jornada (solo estudiante) */}
      {personType === 'estudiante' && (
        <div style={S.fieldGroup}>
          <label style={S.label}>Jornada *</label>
          <select
            style={{ ...S.select, ...(errors.jornada ? S.inputError : {}) }}
            value={fields.jornada}
            onChange={e => handleChange('jornada', e.target.value)}
          >
            <option value="">Seleccionar jornada</option>
            {JORNADAS.map(j => <option key={j} value={j}>{j}</option>)}
          </select>
          {touched.jornada && errors.jornada && <span style={S.errorMsg}>{errors.jornada}</span>}
        </div>
      )}

      {/* Save button */}
      <button
        style={{ ...S.saveBtn, ...(saving ? S.saveBtnDisabled : {}) }}
        onClick={handleSave}
        disabled={saving}
      >
        <MdSave size={15} />
        {saving ? 'Guardando...' : 'Guardar registro'}
      </button>

      {/* Success / error message */}
      {savedMsg && (
        <div style={{
          ...S.savedBox,
          background: savedMsg.type === 'ok' ? 'rgba(46,125,50,0.08)' : 'rgba(198,40,40,0.08)',
          borderColor: savedMsg.type === 'ok' ? 'var(--green)' : 'var(--red)',
          color: savedMsg.type === 'ok' ? 'var(--green)' : 'var(--red)',
        }}>
          {savedMsg.type === 'ok' ? <MdCheckCircle size={16} /> : <MdError size={16} />}
          <span>{savedMsg.text}</span>
          {savedMsg.type === 'ok' && (
            <div style={S.savedActions}>
              <button style={S.actionBtn} onClick={handleAddAnother}>
                <MdAdd size={13} /> Agregar otro
              </button>
              <button style={{ ...S.actionBtn, ...S.actionBtnAlt }} onClick={onGoToList}>
                <MdList size={13} /> Ir al listado
              </button>
            </div>
          )}
        </div>
      )}

      {/* Duplicate modal */}
      {duplicateModal && (
        <div style={S.modalOverlay}>
          <div style={S.modal}>
            <div style={S.modalHeader}>
              <MdWarning size={20} color="var(--gold)" />
              <span>Registro duplicado</span>
            </div>
            <p style={S.modalText}>
              Ya existe un registro con este identificador. ¿Deseas actualizar sus datos?
            </p>
            <div style={S.modalInfo}>
              <span><strong>Nombre actual:</strong> {duplicateModal.nombre}</span>
            </div>
            <div style={S.modalBtns}>
              <button style={S.modalBtnConfirm} onClick={doSave}>
                Sí, actualizar
              </button>
              <button style={S.modalBtnCancel} onClick={() => setDuplicateModal(null)}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Styles ──
const S = {
  container: {
    display: 'flex', flexDirection: 'column', gap: 16,
    padding: 24, maxWidth: 600,
  },
  title: {
    fontSize: 16, fontWeight: 700, color: 'var(--vino-dark)',
    margin: 0, marginBottom: 4,
  },
  fieldGroup: {
    display: 'flex', flexDirection: 'column', gap: 5,
  },
  label: {
    fontSize: 11, fontWeight: 700, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.5px',
  },
  input: {
    padding: '10px 12px', borderRadius: 'var(--radius-sm)',
    border: '1px solid #D5CFC3', background: '#fff',
    fontSize: 13, color: 'var(--text-dark)',
    outline: 'none', transition: 'border-color 0.2s',
    fontFamily: 'var(--font)',
  },
  inputError: {
    borderColor: 'var(--red)',
    background: 'rgba(198,40,40,0.03)',
  },
  inputWarn: {
    borderColor: 'var(--gold)',
    background: 'rgba(201,168,76,0.05)',
  },
  select: {
    padding: '10px 32px 10px 12px', borderRadius: 'var(--radius-sm)',
    border: '1px solid #D5CFC3', background: '#fff',
    fontSize: 13, color: 'var(--text-dark)',
    outline: 'none', cursor: 'pointer',
    fontFamily: 'var(--font)',
  },
  row2: {
    display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12,
  },
  selectRow: {
    display: 'flex', gap: 6, alignItems: 'stretch',
  },
  addGroupBtn: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '0 10px', borderRadius: 'var(--radius-sm)',
    border: '1px dashed var(--vino-light)', background: 'rgba(106,27,41,0.04)',
    color: 'var(--vino)', cursor: 'pointer', transition: 'all 0.2s',
    fontSize: 11, fontWeight: 700,
  },
  errorMsg: {
    fontSize: 11, color: 'var(--red)', fontWeight: 500,
    display: 'flex', alignItems: 'center', gap: 4,
  },
  idWarning: {
    display: 'flex', alignItems: 'center', gap: 5,
    fontSize: 11, color: 'var(--gold)', fontWeight: 600,
    padding: '6px 10px', borderRadius: 'var(--radius-sm)',
    background: 'rgba(201,168,76,0.08)',
    border: '1px solid rgba(201,168,76,0.2)',
    marginTop: -8,
  },
  saveBtn: {
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
    width: '100%', padding: '12px', borderRadius: 'var(--radius-sm)', border: 'none',
    background: 'var(--vino-gradient)', color: 'var(--beige)',
    fontSize: 13, fontWeight: 700, cursor: 'pointer',
    transition: 'filter 0.2s', marginTop: 8, boxShadow: 'var(--shadow-sm)',
  },
  saveBtnDisabled: {
    filter: 'grayscale(60%) opacity(0.75)', cursor: 'not-allowed',
  },
  savedBox: {
    display: 'flex', flexDirection: 'column', gap: 10,
    padding: '14px 16px', borderRadius: 'var(--radius-sm)',
    border: '1px solid', fontSize: 13, fontWeight: 600,
  },
  savedActions: {
    display: 'flex', gap: 8, marginTop: 4,
  },
  actionBtn: {
    display: 'flex', alignItems: 'center', gap: 4,
    padding: '7px 14px', borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--vino)', background: 'var(--vino)',
    color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer',
    transition: 'all 0.2s',
  },
  actionBtnAlt: {
    background: 'transparent', color: 'var(--vino)',
  },
  // Modal
  modalOverlay: {
    position: 'fixed', inset: 0, zIndex: 1000,
    background: 'rgba(0,0,0,0.45)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    backdropFilter: 'blur(3px)',
  },
  modal: {
    background: '#fff', borderRadius: 'var(--radius)',
    padding: '28px 28px 22px', maxWidth: 420, width: '90%',
    boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
  },
  modalHeader: {
    display: 'flex', alignItems: 'center', gap: 8,
    fontSize: 16, fontWeight: 700, color: 'var(--vino-dark)',
    marginBottom: 12,
  },
  modalText: {
    fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6,
    margin: '0 0 12px',
  },
  modalInfo: {
    fontSize: 12, color: 'var(--text-dark)',
    padding: '8px 12px', borderRadius: 'var(--radius-sm)',
    background: 'var(--beige)', marginBottom: 18,
  },
  modalBtns: {
    display: 'flex', gap: 8, justifyContent: 'flex-end',
  },
  modalBtnConfirm: {
    padding: '9px 18px', borderRadius: 'var(--radius-sm)',
    border: 'none', background: 'var(--vino)', color: '#fff',
    fontSize: 12, fontWeight: 700, cursor: 'pointer',
  },
  modalBtnCancel: {
    padding: '9px 18px', borderRadius: 'var(--radius-sm)',
    border: '1px solid #D5CFC3', background: '#fff', color: 'var(--text-muted)',
    fontSize: 12, fontWeight: 600, cursor: 'pointer',
  },
}
