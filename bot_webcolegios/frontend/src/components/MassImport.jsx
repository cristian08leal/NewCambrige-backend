// =============================================================================
// components/MassImport.jsx — Importación masiva desde archivo
// =============================================================================
import { useState, useEffect, useRef } from 'react'
import {
  MdUploadFile, MdDownload, MdCheckCircle, MdCancel, MdPlayArrow,
  MdClose, MdInsertDriveFile, MdWarning, MdError, MdAutorenew
} from 'react-icons/md'
import { FiLoader } from 'react-icons/fi'
import { useImport } from './ImportContext'
import { parseFile, getFileExtension } from '../utils/fileParser'
import { mapColumns, applyMapping, FIELD_LABELS } from '../utils/columnMapper'
import { downloadTemplate } from '../utils/templateGenerator'

// Steps: idle → preview → processing → done/error
const STEPS = { IDLE: 'idle', PREVIEW: 'preview', PROCESSING: 'processing', DONE: 'done' }

export default function MassImport() {
  const { personType } = useImport()
  const fileRef = useRef(null)

  const [step, setStep] = useState(STEPS.IDLE)
  const [file, setFile] = useState(null)
  const [fileError, setFileError] = useState(null)
  const [parsedData, setParsedData] = useState([])
  const [columns, setColumns] = useState([])
  const [mapping, setMapping] = useState({})
  const [unmapped, setUnmapped] = useState([])
  const [previewRows, setPreviewRows] = useState([])
  const [processLog, setProcessLog] = useState([])
  const [processResult, setProcessResult] = useState(null)
  const [isDragging, setIsDragging] = useState(false)

  const logRef = useRef(null)

  // Reset when person type changes
  useEffect(() => {
    resetAll()
  }, [personType])

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [processLog])

  const resetAll = () => {
    setStep(STEPS.IDLE)
    setFile(null)
    setFileError(null)
    setParsedData([])
    setColumns([])
    setMapping({})
    setUnmapped([])
    setPreviewRows([])
    setProcessLog([])
    setProcessResult(null)
  }

  // ── File handling ──
  const handleFile = async (f) => {
    setFileError(null)
    const ext = getFileExtension(f.name)
    if (!ext) {
      setFileError('Formato no válido. Solo se aceptan archivos CSV, Excel o JSON.')
      return
    }

    setFile(f)
    const result = await parseFile(f)

    if (result.error) {
      setFileError(result.error)
      return
    }

    if (result.data.length === 0) {
      setFileError('El archivo no contiene datos.')
      return
    }

    // Map columns
    const { mapping: m, unmapped: u } = mapColumns(result.columns, personType)

    // Check unmapped required fields
    if (u.length > 0) {
      const fieldName = FIELD_LABELS[u[0]] || u[0]
      setFileError(`No se pudo identificar la columna '${fieldName}'. Por favor usa la plantilla descargable o renombra la columna.`)
      return
    }

    setParsedData(result.data)
    setColumns(result.columns)
    setMapping(m)
    setUnmapped(u)

    // Preview first 5 rows mapped
    const preview = result.data.slice(0, 5).map(row => applyMapping(row, m))
    setPreviewRows(preview)
    setStep(STEPS.PREVIEW)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true) }
  const onDragLeave = () => setIsDragging(false)

  const onSelectFile = (e) => {
    const f = e.target.files[0]
    if (f) handleFile(f)
  }

  // ── Process ──
  const handleProcess = async () => {
    setStep(STEPS.PROCESSING)
    setProcessLog([])
    setProcessResult(null)

    // Map all rows
    const allMapped = parsedData.map(row => applyMapping(row, mapping))

    // Send to backend
    const body = {
      tipo: personType,
      registros: allMapped.map(row => ({
        nombre: row.nombre,
        codigo_interno: row.codigo_interno || null,
        documento_nacional: row.documento_nacional || null,
        grado: row.grado || null,
        curso: row.curso || null,
        jornada: row.jornada || null,
      }))
    }

    try {
      const res = await fetch('/api/import/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': 'dev-secret-key-12345' },
        body: JSON.stringify(body)
      })
      const data = await res.json()

      // Build log with animation
      if (data.log && data.log.length > 0) {
        for (let i = 0; i < data.log.length; i++) {
          await new Promise(r => setTimeout(r, 80))
          setProcessLog(prev => [...prev, data.log[i]])
        }
      }

      await new Promise(r => setTimeout(r, 300))
      setProcessResult(data)
      setStep(STEPS.DONE)
    } catch {
      setProcessResult({
        status: 'error',
        message: 'Error de conexión con el servidor.',
        log: []
      })
      setStep(STEPS.DONE)
    }
  }

  // ── Fields info for preview ──
  const systemFields = personType === 'estudiante'
    ? ['nombre', 'codigo_interno', 'documento_nacional', 'grado', 'curso', 'jornada']
    : ['nombre', 'codigo_interno', 'documento_nacional', 'grado', 'curso']

  return (
    <div style={S.container}>
      {/* Header with download template button */}
      <div style={S.header}>
        <h3 style={S.title}>
          <MdUploadFile size={20} style={{ marginRight: 6, verticalAlign: 'middle', marginTop: -2 }} />
          Importación Masiva — {personType === 'estudiante' ? 'Estudiantes' : 'Docentes'}
        </h3>
        <button
          style={S.downloadBtn}
          onClick={() => downloadTemplate(personType)}
        >
          <MdDownload size={14} />
          Descargar plantilla {personType === 'estudiante' ? 'Estudiante' : 'Docente'}
        </button>
      </div>

      {/* STEP: IDLE — File upload */}
      {step === STEPS.IDLE && (
        <>
          <div
            style={{
              ...S.dropzone,
              ...(isDragging ? S.dropzoneActive : {}),
              ...(fileError ? S.dropzoneError : {})
            }}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onClick={() => fileRef.current?.click()}
          >
            <MdUploadFile size={36} color={isDragging ? 'var(--vino)' : 'var(--text-muted)'} />
            <span style={S.dropText}>
              Arrastra tu archivo aquí o <strong>haz clic para seleccionar</strong>
            </span>
            <span style={S.dropFormats}>
              Formatos aceptados: .csv, .xlsx, .xls, .json
            </span>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,.xlsx,.xls,.json"
              style={{ display: 'none' }}
              onChange={onSelectFile}
            />
          </div>
          {fileError && (
            <div style={S.errorBanner}>
              <MdError size={15} />
              {fileError}
            </div>
          )}
        </>
      )}

      {/* STEP: PREVIEW — Show mapped columns and first 5 rows */}
      {step === STEPS.PREVIEW && (
        <div style={S.previewWrap}>
          <div style={S.fileInfo}>
            <MdInsertDriveFile size={15} color="var(--vino)" />
            <span style={{ fontWeight: 600 }}>{file?.name}</span>
            <span style={S.fileCount}>{parsedData.length} registros detectados</span>
            <button style={S.removeFile} onClick={resetAll}><MdClose size={13} /></button>
          </div>

          {/* Column mapping indicator */}
          <div style={S.mappingRow}>
            <span style={S.mappingLabel}>Mapeo de columnas:</span>
            <div style={S.mappingChips}>
              {systemFields.map(field => {
                const mapped = mapping[field]
                const ok = !!mapped
                return (
                  <div key={field} style={{
                    ...S.chip,
                    background: ok ? 'rgba(46,125,50,0.08)' : 'rgba(198,40,40,0.08)',
                    borderColor: ok ? 'var(--green)' : 'var(--red)',
                    color: ok ? 'var(--green)' : 'var(--red)',
                  }}>
                    {ok ? <MdCheckCircle size={12} /> : <MdCancel size={12} />}
                    <span>{FIELD_LABELS[field] || field}</span>
                    {ok && <span style={S.chipSub}>← {mapped}</span>}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Preview table */}
          <div style={S.previewTableWrap}>
            <table style={S.previewTable}>
              <thead>
                <tr>
                  <th style={S.pth}>#</th>
                  {systemFields.map(f => (
                    <th key={f} style={S.pth}>{FIELD_LABELS[f] || f}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewRows.map((row, i) => (
                  <tr key={i} style={i % 2 === 0 ? {} : { background: 'var(--beige-light)' }}>
                    <td style={S.ptd}>{i + 1}</td>
                    {systemFields.map(f => (
                      <td key={f} style={{
                        ...S.ptd,
                        ...(row[f] ? {} : { color: 'var(--text-muted)', fontStyle: 'italic' })
                      }}>
                        {row[f] || '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={S.previewNote}>
            Mostrando las primeras {previewRows.length} de {parsedData.length} filas
          </div>

          {/* Action buttons */}
          <div style={S.previewActions}>
            <button style={S.processBtn} onClick={handleProcess}>
              <MdPlayArrow size={16} /> Confirmar y procesar
            </button>
            <button style={S.cancelBtn} onClick={resetAll}>
              <MdCancel size={14} /> Cancelar
            </button>
          </div>
        </div>
      )}

      {/* STEP: PROCESSING — Log terminal */}
      {(step === STEPS.PROCESSING || step === STEPS.DONE) && (
        <div style={S.terminalWrap}>
          <div style={S.termHeader}>
            <span style={S.termTitle}>
              {step === STEPS.PROCESSING && (
                <span style={{ display: 'inline-flex', animation: 'spin 0.9s linear infinite', marginRight: 6 }}>
                  <FiLoader size={13} />
                </span>
              )}
              Procesando {parsedData.length} registros...
            </span>
          </div>
          <div ref={logRef} style={S.termBody}>
            {processLog.map((entry, i) => {
              let iconElem, color
              if (entry.estado === 'admitido') {
                iconElem = <MdCheckCircle size={12} style={{ marginRight: 5 }} />; color = '#66BB6A'
              } else if (entry.estado === 'actualizado') {
                iconElem = <MdAutorenew size={12} style={{ marginRight: 5 }} />; color = '#90CAF9'
              } else {
                iconElem = <MdError size={12} style={{ marginRight: 5 }} />; color = '#EF5350'
              }
              return (
                <div key={i} style={{ fontFamily: 'var(--mono)', fontSize: 12, lineHeight: 1.8, color, display: 'flex', alignItems: 'center' }}>
                  {iconElem} Fila {entry.fila} — {entry.nombre} — {
                    entry.estado === 'admitido' ? 'Admitido' :
                    entry.estado === 'actualizado' ? 'Actualizado' :
                    `Rechazado: ${entry.razon}`
                  }
                </div>
              )
            })}
            {step === STEPS.PROCESSING && processLog.length === 0 && (
              <div style={{ color: '#555', fontSize: 12 }}>
                Enviando datos al servidor...
              </div>
            )}
          </div>

          {/* Result message */}
          {processResult && (
            <div style={{
              ...S.resultBanner,
              background: processResult.status === 'completed'
                ? 'rgba(46,125,50,0.08)' : 'rgba(198,40,40,0.08)',
              borderColor: processResult.status === 'completed'
                ? 'var(--green)' : 'var(--red)',
              color: processResult.status === 'completed'
                ? 'var(--green)' : 'var(--red)',
            }}>
              {processResult.status === 'completed'
                ? <MdCheckCircle size={16} />
                : <MdWarning size={16} />}
              <span>{processResult.message}</span>
            </div>
          )}

          {step === STEPS.DONE && (
            <div style={{ padding: '16px', background: 'var(--beige-light)' }}>
              <h4 style={{ margin: '0 0 10px 0', fontSize: 13, color: 'var(--vino-dark)' }}>Resumen de Importación</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 15 }}>
                <div style={{ padding: 10, background: 'rgba(46,125,50,0.1)', border: '1px solid var(--green)', borderRadius: 6, textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--green)' }}>
                    {processLog.filter(l => l.estado === 'admitido').length}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--green)', fontWeight: 600 }}>Nuevos Admitidos</div>
                </div>
                <div style={{ padding: 10, background: 'rgba(25,118,210,0.1)', border: '1px solid #1976D2', borderRadius: 6, textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#1976D2' }}>
                    {processLog.filter(l => l.estado === 'actualizado').length}
                  </div>
                  <div style={{ fontSize: 11, color: '#1976D2', fontWeight: 600 }}>Actualizados</div>
                </div>
                <div style={{ padding: 10, background: 'rgba(198,40,40,0.1)', border: '1px solid var(--red)', borderRadius: 6, textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--red)' }}>
                    {processLog.filter(l => l.estado === 'rechazado').length}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--red)', fontWeight: 600 }}>Rechazados</div>
                </div>
              </div>
              
              {processLog.filter(l => l.estado === 'rechazado').length > 0 && (
                <div style={{ maxHeight: 150, overflowY: 'auto', border: '1px solid #E5DFD3', borderRadius: 6, background: '#fff' }}>
                  <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        <th style={{ padding: 8, background: '#F5F5F5', borderBottom: '1px solid #ddd', textAlign: 'left' }}>Fila</th>
                        <th style={{ padding: 8, background: '#F5F5F5', borderBottom: '1px solid #ddd', textAlign: 'left' }}>Nombre</th>
                        <th style={{ padding: 8, background: '#F5F5F5', borderBottom: '1px solid #ddd', textAlign: 'left' }}>Motivo de Rechazo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {processLog.filter(l => l.estado === 'rechazado').map((l, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                          <td style={{ padding: '6px 8px' }}>{l.fila}</td>
                          <td style={{ padding: '6px 8px' }}>{l.nombre}</td>
                          <td style={{ padding: '6px 8px', color: 'var(--red)' }}>{l.razon}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div style={{ marginTop: 16 }}>
                <button style={S.resetBtn} onClick={resetAll}>
                  <MdUploadFile size={14} /> Cargar otro archivo
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Styles ──
const S = {
  container: {
    display: 'flex', flexDirection: 'column', gap: 16,
    padding: 24, height: '100%', overflow: 'auto',
  },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    flexWrap: 'wrap', gap: 10,
  },
  title: {
    fontSize: 16, fontWeight: 700, color: 'var(--vino-dark)', margin: 0,
  },
  downloadBtn: {
    display: 'flex', alignItems: 'center', gap: 5,
    padding: '8px 14px', borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--vino)', background: 'rgba(106,27,41,0.04)',
    color: 'var(--vino)', fontSize: 12, fontWeight: 600, cursor: 'pointer',
    transition: 'all 0.2s',
  },
  // Dropzone
  dropzone: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    gap: 10, padding: '48px 24px',
    border: '2px dashed #D5CFC3', borderRadius: 'var(--radius)',
    background: 'rgba(246,244,238,0.5)', cursor: 'pointer',
    transition: 'all 0.25s',
  },
  dropzoneActive: {
    borderColor: 'var(--vino)', background: 'rgba(106,27,41,0.04)',
  },
  dropzoneError: {
    borderColor: 'var(--red)', background: 'rgba(198,40,40,0.03)',
  },
  dropText: {
    fontSize: 13, color: 'var(--text-muted)', textAlign: 'center',
  },
  dropFormats: {
    fontSize: 11, color: 'var(--text-muted)', opacity: 0.7,
  },
  errorBanner: {
    display: 'flex', alignItems: 'center', gap: 8,
    padding: '10px 14px', borderRadius: 'var(--radius-sm)',
    background: 'rgba(198,40,40,0.08)', color: 'var(--red)',
    fontSize: 12, fontWeight: 600,
    border: '1px solid rgba(198,40,40,0.15)',
  },
  // Preview
  previewWrap: {
    display: 'flex', flexDirection: 'column', gap: 14,
  },
  fileInfo: {
    display: 'flex', alignItems: 'center', gap: 8,
    padding: '10px 14px', borderRadius: 'var(--radius-sm)',
    background: 'rgba(106,27,41,0.04)',
    border: '1px solid rgba(106,27,41,0.12)',
    fontSize: 13, color: 'var(--text-dark)',
  },
  fileCount: {
    marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)', fontWeight: 600,
  },
  removeFile: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: 22, height: 22, borderRadius: '50%',
    border: 'none', background: 'rgba(0,0,0,0.08)',
    cursor: 'pointer', color: 'var(--text-muted)',
  },
  mappingRow: {
    display: 'flex', flexDirection: 'column', gap: 8,
  },
  mappingLabel: {
    fontSize: 11, fontWeight: 700, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.5px',
  },
  mappingChips: {
    display: 'flex', flexWrap: 'wrap', gap: 6,
  },
  chip: {
    display: 'flex', alignItems: 'center', gap: 4,
    padding: '4px 10px', borderRadius: 20,
    border: '1px solid', fontSize: 11, fontWeight: 600,
  },
  chipSub: {
    fontSize: 10, opacity: 0.7, fontWeight: 400,
  },
  previewTableWrap: {
    borderRadius: 'var(--radius-sm)', overflow: 'auto',
    border: '1px solid #E5DFD3', maxHeight: 220,
  },
  previewTable: {
    width: '100%', borderCollapse: 'collapse', fontSize: 12,
  },
  pth: {
    padding: '9px 12px', background: 'var(--vino-dim)', color: 'var(--vino-dark)',
    fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.7px',
    position: 'sticky', top: 0, whiteSpace: 'nowrap',
    borderBottom: '2px solid rgba(106,27,41,0.1)', textAlign: 'left',
  },
  ptd: {
    padding: '8px 12px', color: 'var(--text-dark)', whiteSpace: 'nowrap',
    borderBottom: '1px solid #F0ECE1',
  },
  previewNote: {
    fontSize: 11, color: 'var(--text-muted)', textAlign: 'center',
    fontStyle: 'italic',
  },
  previewActions: {
    display: 'flex', gap: 10, justifyContent: 'center',
  },
  processBtn: {
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '11px 24px', borderRadius: 'var(--radius-sm)', border: 'none',
    background: 'var(--vino-gradient)', color: 'var(--beige)',
    fontSize: 13, fontWeight: 700, cursor: 'pointer',
    boxShadow: 'var(--shadow-sm)',
  },
  cancelBtn: {
    display: 'flex', alignItems: 'center', gap: 5,
    padding: '10px 18px', borderRadius: 'var(--radius-sm)',
    border: '1px solid #D5CFC3', background: '#fff',
    color: 'var(--text-muted)', fontSize: 12, fontWeight: 600, cursor: 'pointer',
  },
  // Terminal
  terminalWrap: {
    borderRadius: 'var(--radius-sm)', overflow: 'hidden',
    border: '1px solid #2A2A2A', flex: 1, display: 'flex', flexDirection: 'column',
    minHeight: 280,
  },
  termHeader: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '9px 16px', background: '#1E1E1E', borderBottom: '1px solid #2C2C2C',
  },
  termTitle: {
    display: 'flex', alignItems: 'center', fontSize: 12, fontWeight: 600, color: '#CCC',
  },
  termBody: {
    flex: 1, padding: '12px 16px', overflowY: 'auto', background: '#111',
    maxHeight: 320,
  },
  resultBanner: {
    display: 'flex', alignItems: 'center', gap: 8,
    padding: '12px 16px', fontSize: 13, fontWeight: 700,
    border: '1px solid', margin: '0',
  },
  resetBtn: {
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '9px 16px', borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--vino)', background: 'rgba(106,27,41,0.04)',
    color: 'var(--vino)', fontSize: 12, fontWeight: 600, cursor: 'pointer',
  },
}
