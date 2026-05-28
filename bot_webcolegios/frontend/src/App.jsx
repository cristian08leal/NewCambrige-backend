import { useState, useEffect, useRef, useCallback } from 'react'
import {
  MdSchool, MdPeople, MdPlayArrow, MdStop, MdRefresh, MdDelete,
  MdCircle, MdDataset, MdUploadFile, MdEditNote, MdConstruction,
  MdChevronRight, MdTableChart, MdTerminal, MdBarChart,
} from 'react-icons/md'
import { FiLoader } from 'react-icons/fi'
import { ImportProvider } from './components/ImportContext'
import PersonTypeSelector from './components/PersonTypeSelector'
import MassImport from './components/MassImport'
import ManualImport from './components/ManualImport'

// ── API helpers ──────────────────────────────────────────────────────────
const API_KEY = 'dev-secret-key-12345'
const authHeaders = { 'X-API-Key': API_KEY }
const api = {
  status:  () => fetch('/api/status').then(r => r.json()),
  health:  () => fetch('/api/health').then(r => r.json()),
  stats:   () => fetch('/api/stats').then(r => r.json()),
  logs:    (offset) => fetch(`/api/logs?offset=${offset}`).then(r => r.json()),
  data:    (tipo) => fetch(`/api/data/${tipo}`).then(r => r.json()),
  scrape:  (tipo) => fetch(`/api/scrape/${tipo}`, { method: 'POST', headers: authHeaders }).then(r => r.json()),
  clearLogs: () => fetch('/api/clear-logs', { method: 'POST', headers: authHeaders }),
}

// ── Columns config ───────────────────────────────────────────────────────
const COLS = {
  estudiantes: ['id','documento','nombre','grado_texto','curso','jornada','titular'],
  docentes:    ['id','documento','nombre','grado_titular','curso_titular'],
}
const LABELS = {
  id:'#', documento:'Documento', nombre:'Nombre Completo',
  grado_texto:'Grado', curso:'Curso', jornada:'Jornada', titular:'Titular',
  grado_titular:'Grado Titular', curso_titular:'Curso',
}

const METHODS = [
  { id: 'scraping', label: 'Scraping WebColegios', icon: MdDataset, available: true },
  { id: 'csv',      label: 'Importación Masiva',   icon: MdUploadFile, available: true },
  { id: 'manual',   label: 'Ingreso Manual',       icon: MdEditNote,  available: true },
]

// ── Log level classifier ─────────────────────────────────────────────────
const getLogClass = (line) => {
  if (/\[ERROR\]/.test(line))   return 'log-err'
  if (/\[WARNING\]/.test(line)) return 'log-warn'
  if (/finalizado|completado/i.test(line)) return 'log-ok'
  if (/\[INFO\]/.test(line))    return 'log-info'
  return 'log-dim'
}

// ── Spinner component ────────────────────────────────────────────────────
function Spinner() {
  return (
    <span style={{ display:'inline-flex', animation:'spin 0.9s linear infinite' }}>
      <FiLoader size={14}/>
    </span>
  )
}

export default function App() {
  const [method,       setMethod]       = useState('scraping')
  const [dataType,     setDataType]     = useState('estudiantes')
  const [status,       setStatus]       = useState({ running: false, tipo: null })
  const [stats,        setStats]        = useState({ estudiantes: '—', docentes: '—' })
  const [logs,         setLogs]         = useState([])
  const [tableData,    setTableData]    = useState([])
  const [tableType,    setTableType]    = useState('estudiantes')
  const [tableLoading, setTableLoading] = useState(false)
  const [activeTab,    setActiveTab]    = useState('estudiantes')
  const [health,       setHealth]       = useState('ok')

  const logOffset = useRef(0)
  const pollRef = useRef(null)
  const termRef = useRef(null)

  // Auto-load on mount
  useEffect(() => { loadData('estudiantes') }, [])

  // Polling logs when scraping runs
  const pollLogs = useCallback(async () => {
    try {
      const d = await api.logs(logOffset.current)
      if (d.logs?.length) {
        const cleaned = d.logs.map(l => l.trimEnd()).filter(l => l.length > 0)
        setLogs(prev => [...prev, ...cleaned.map(text => ({ text, raw: true }))])
        logOffset.current = d.next_offset
      }
    } catch {}
  }, [])

  // Status polling
  useEffect(() => {
    let prev = false
    const tick = async () => {
      try {
        const s = await api.status()
        setStatus(s)
        if (s.running && !pollRef.current) {
          pollRef.current = setInterval(pollLogs, 1000)
        }
        if (!s.running && prev) {
          clearInterval(pollRef.current); pollRef.current = null
          await pollLogs()
          loadStats()
          if (activeTab) loadData(activeTab)
        }
        prev = s.running
      } catch {}
    }
    tick()
    const id = setInterval(tick, 2000)
    return () => { clearInterval(id); clearInterval(pollRef.current) }
  }, [pollLogs, activeTab])

  // Auto-scroll terminal
  useEffect(() => {
    if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight
  }, [logs])

  // Stats & Health
  const loadStats = async () => {
    try { const d = await api.stats(); setStats(d) } catch {}
  }
  const loadHealth = async () => {
    try {
      const d = await api.health()
      setHealth(d.status === 'ok' ? 'ok' : 'error')
    } catch {
      setHealth('error')
    }
  }
  useEffect(() => {
    loadStats()
    loadHealth()
    const idStats = setInterval(loadStats, 30000)
    const idHealth = setInterval(loadHealth, 30000)
    return () => { clearInterval(idStats); clearInterval(idHealth) }
  }, [])

  // Load table data
  const loadData = async (tipo) => {
    setActiveTab(tipo); setTableType(tipo); setTableLoading(true)
    try {
      const d = await api.data(tipo)
      setTableData(d.data || [])
    } catch { setTableData([]) }
    finally { setTableLoading(false) }
  }

  // Start scraping
  const handleStart = async () => {
    if (method !== 'scraping') return
    await api.clearLogs()
    logOffset.current = 0
    setLogs([{ text: `> Iniciando extraccion de ${dataType.toUpperCase()} desde WebColegios...`, raw: false, cls: 'log-warn' }])
    try {
      const d = await api.scrape(dataType)
      if (d.status !== 'ok') {
        setLogs(prev => [...prev, { text: `ERROR: ${d.message}`, cls: 'log-err', raw: false }])
      }
    } catch {
      setLogs(prev => [...prev, { text: 'ERROR: No se pudo contactar el servidor local.', cls: 'log-err', raw: false }])
    }
  }

  const handleClearLogs = () => setLogs([])

  // "Ir al listado" handler for ManualImport
  const handleGoToList = () => {
    const tipo = dataType === 'estudiantes' ? 'estudiantes' : 'docentes'
    loadData(tipo)
    // Optionally switch to scraping view to show the table
    // setMethod('scraping')
  }

  const isRunning = status.running

  return (
    <ImportProvider>
      <div style={S.root}>
        {/* ── NAVBAR ── */}
        <nav style={S.nav}>
          <div style={S.brand}>
            <MdSchool size={26} color="var(--gold-light)" />
            <span style={S.brandTitle}>
              WebColegios <span style={{ color: 'var(--gold-light)' }}>Bot</span>
            </span>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:10 }}>
            <StatPill icon={<MdSchool size={13}/>} label={`${stats.estudiantes} Estudiantes`} />
            <StatPill icon={<MdPeople size={13}/>} label={`${stats.docentes} Docentes`} />
            <StatusBadge status={status} />
          </div>
        </nav>

        {health === 'error' && (
          <div style={{ background: 'var(--vino)', color: 'var(--beige)', padding: '10px 24px', fontSize: 13, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            ⚠️ Problema de conexión. El servidor o la base de datos no responden correctamente.
          </div>
        )}

        {/* ── BODY ── */}
        <div style={S.body}>

          {/* ── SIDEBAR ── */}
          <aside style={S.sidebar}>

            <Section icon={<MdDataset size={14}/>} label="Origen de Datos">
              {METHODS.map(m => (
                <button
                  key={m.id}
                  style={{ ...S.methodBtn, ...(method === m.id ? S.methodBtnActive : {}) }}
                  onClick={() => m.available && setMethod(m.id)}
                  disabled={isRunning || !m.available}
                >
                  <m.icon size={14}/>
                  <span>{m.label}</span>
                  {!m.available && <span style={S.soonBadge}>Pronto</span>}
                  {method === m.id && m.available && <MdChevronRight size={14} style={{ marginLeft:'auto' }}/>}
                </button>
              ))}
            </Section>

            {/* Person type selector for import modes */}
            {(method === 'csv' || method === 'manual') && (
              <PersonTypeSelector disabled={isRunning} />
            )}

            {/* Scraping mode: group selector + run button */}
            {method === 'scraping' && (
              <>
                <Section icon={<MdPeople size={14}/>} label="Grupo a Extraer">
                  <div style={S.typeRow}>
                    {['estudiantes','docentes'].map(t => (
                      <button
                        key={t}
                        style={{ ...S.typeBtn, ...(dataType === t ? S.typeBtnActive : {}) }}
                        onClick={() => setDataType(t)}
                        disabled={isRunning}
                      >
                        {t === 'estudiantes'
                          ? <><MdSchool size={13}/> Estudiantes</>
                          : <><MdPeople size={13}/> Docentes</>}
                      </button>
                    ))}
                  </div>
                </Section>

                <Section icon={<MdPlayArrow size={14}/>} label="Ejecutar Extraccion">
                  <p style={S.desc}>
                    {dataType === 'estudiantes'
                      ? 'Obtiene la lista oficial de alumnos activos desde WebColegios y actualiza la base de datos.'
                      : 'Descarga listados oficiales para asignar los grados titulares de cada docente.'}
                  </p>
                  <button
                    style={{ ...S.runBtn, ...(isRunning ? S.runBtnDisabled : {}) }}
                    onClick={handleStart}
                    disabled={isRunning}
                  >
                    {isRunning && status.tipo === dataType
                      ? <><Spinner /> Extrayendo {dataType}...</>
                      : <><MdPlayArrow size={15}/> Iniciar Extraccion de {dataType.charAt(0).toUpperCase() + dataType.slice(1)}</>}
                  </button>
                </Section>
              </>
            )}

            <Section icon={<MdTableChart size={14}/>} label="Ver Tabla">
              <div style={S.typeRow}>
                {['estudiantes','docentes'].map(t => (
                  <button
                    key={t}
                    style={{ ...S.typeBtn, ...(activeTab === t ? S.typeBtnActive : {}) }}
                    onClick={() => loadData(t)}
                  >
                    {t === 'estudiantes' ? 'Estudiantes' : 'Docentes'}
                  </button>
                ))}
              </div>
            </Section>

          </aside>

          {/* ── RIGHT PANEL ── */}
          <div style={S.right}>

            {/* Import modules render in the right panel */}
            {method === 'csv' && (
              <div style={S.importPanel}>
                <MassImport />
              </div>
            )}

            {method === 'manual' && (
              <div style={S.importPanel}>
                <ManualImport onGoToList={handleGoToList} />
              </div>
            )}

            {/* Terminal (only for scraping mode) */}
            {method === 'scraping' && (
              <div style={S.termWrap}>
                <div style={S.panelHeader}>
                  <span style={S.panelTitle}>
                    <MdTerminal size={14} style={{ marginRight:6 }}/>
                    Terminal de Procesos
                    <span style={{ color:'#555', marginLeft:8, fontWeight:400 }}>WebColegios Bot</span>
                  </span>
                  <button style={S.clearBtn} onClick={handleClearLogs}>
                    <MdDelete size={12}/> Limpiar
                  </button>
                </div>
                <div ref={termRef} style={S.termBody}>
                  {logs.length === 0 && (
                    <div style={{ color:'#555', fontSize:12 }}>
                      Sistema listo. Selecciona una opcion en el menu lateral para comenzar.
                      <span style={S.cursor} />
                    </div>
                  )}
                  {logs.map((l, i) => {
                    const cls = l.raw ? getLogClass(l.text) : (l.cls || 'log-dim')
                    return <div key={i} className={cls} style={{ fontFamily:'var(--mono)', fontSize:12, lineHeight:1.75 }}>{l.text}</div>
                  })}
                </div>
              </div>
            )}

            {/* Data Table */}
            <div style={S.tableWrap}>
              <div style={S.panelHeaderWhite}>
                <span style={S.panelTitleDark}>
                  {tableType === 'estudiantes'
                    ? <><MdSchool size={16} style={{ verticalAlign:'middle', marginRight:6 }}/>Listado Oficial de Estudiantes</>
                    : <><MdPeople size={16} style={{ verticalAlign:'middle', marginRight:6 }}/>Listado Oficial de Docentes</>}
                </span>
                <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                  <span style={S.countPillDark}>
                    <MdBarChart size={12} style={{ verticalAlign:'middle', marginRight:4 }}/>
                    {tableData.length} registros sincronizados
                  </span>
                  <button style={S.reloadBtn} onClick={() => loadData(activeTab)}>
                    <MdRefresh size={13}/> Recargar tabla
                  </button>
                </div>
              </div>
              <div style={S.tableScroll}>
                {tableLoading ? (
                  <div style={S.emptyState}>
                    <Spinner /> Cargando desde la base de datos...
                  </div>
                ) : tableData.length === 0 ? (
                  <div style={S.emptyState}>
                    Sin registros. Ejecuta la extraccion para poblar la base de datos.
                  </div>
                ) : (
                  <DataTable data={tableData} tipo={tableType} />
                )}
              </div>
            </div>

          </div>
        </div>
      </div>
    </ImportProvider>
  )
}

// ── Sub-components ───────────────────────────────────────────────────────

function StatPill({ icon, label }) {
  return (
    <div style={S.statPill}>
      {icon}
      <span style={{ marginLeft:5 }}>{label}</span>
    </div>
  )
}

function StatusBadge({ status }) {
  const running = status.running
  return (
    <div style={{
      ...S.badge,
      background: running ? 'rgba(232,205,125,0.15)' : 'rgba(255,255,255,0.08)',
      color:      running ? 'var(--gold-light)'       : 'var(--beige-dark)',
      border:     running ? '1px solid var(--gold-light)' : '1px solid rgba(255,255,255,0.15)',
    }}>
      {running
        ? <><Spinner /> EJECUTANDO: {(status.tipo||'').toUpperCase()}</>
        : <><MdCircle size={8} style={{ marginRight:5 }}/> SISTEMA INACTIVO</>}
    </div>
  )
}

function Section({ icon, label, children }) {
  return (
    <div style={S.section}>
      <div style={S.sectionLabel}>
        <span style={{ marginRight:5, opacity:0.7 }}>{icon}</span>
        {label}
      </div>
      {children}
    </div>
  )
}

function DataTable({ data, tipo }) {
  const cols = COLS[tipo] || []
  return (
    <table style={S.table}>
      <thead>
        <tr>
          {cols.map(c => <th key={c} style={S.th}>{LABELS[c]||c}</th>)}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i} style={i%2===0 ? {} : { background:'var(--beige-light)' }}>
            {cols.map(c => {
              const val = row[c]
              const empty = val === null || val === undefined || val === ''
              if (empty) return <td key={c} style={{ ...S.td, ...S.nullVal }}>—</td>
              if (c === 'grado_texto' || c === 'grado_titular')
                return <td key={c} style={S.td}><span style={S.badgeGrade}>{val}</span></td>
              if (c === 'curso' || c === 'curso_titular')
                return <td key={c} style={S.td}><span style={S.badgeCurso}>{val}</span></td>
              return <td key={c} style={S.td}>{val}</td>
            })}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// ── Styles ───────────────────────────────────────────────────────────────
const S = {
  root: { display:'flex', flexDirection:'column', height:'100vh', overflow:'hidden' },

  nav: {
    display:'flex', alignItems:'center', justifyContent:'space-between',
    padding:'0 24px', height:58, flexShrink:0,
    background:'var(--vino-gradient)',
    boxShadow:'var(--shadow)', zIndex:10,
  },
  brand:      { display:'flex', alignItems:'center', gap:10 },
  brandTitle: { fontSize:'1.05rem', fontWeight:800, color:'var(--beige)', letterSpacing:'-0.3px' },

  statPill: {
    display:'flex', alignItems:'center',
    padding:'5px 12px', borderRadius:20, fontSize:12, fontWeight:600,
    background:'rgba(255,255,255,0.1)', border:'1px solid rgba(255,255,255,0.18)', color:'var(--beige)',
  },
  badge: {
    display:'flex', alignItems:'center', gap:5,
    padding:'5px 12px', borderRadius:20, fontSize:11, fontWeight:700, letterSpacing:'0.4px',
  },

  body: { display:'grid', gridTemplateColumns:'270px 1fr', flex:1, overflow:'hidden' },

  sidebar: {
    padding:'18px 16px', display:'flex', flexDirection:'column', gap:22,
    background:'var(--beige-light)', borderRight:'1px solid #E5DFD3', overflowY:'auto',
  },
  section: { display:'flex', flexDirection:'column', gap:10 },
  sectionLabel: {
    display:'flex', alignItems:'center',
    fontSize:10, fontWeight:800, textTransform:'uppercase', letterSpacing:'1.2px',
    color:'var(--vino)', paddingBottom:8, borderBottom:'2px solid var(--vino)',
  },

  methodBtn: {
    display:'flex', alignItems:'center', gap:8,
    width:'100%', padding:'9px 12px', borderRadius:'var(--radius-sm)',
    border:'1px solid #D5CFC3', background:'var(--beige)',
    color:'var(--text-dark)', fontSize:12, fontWeight:500, cursor:'pointer',
    transition:'all 0.18s', textAlign:'left',
  },
  methodBtnActive: {
    background:'var(--vino)', border:'1px solid var(--vino-dark)',
    color:'var(--beige)', fontWeight:700,
  },
  methodBtnDisabled: { opacity:0.5, cursor:'not-allowed' },
  soonBadge: {
    marginLeft:'auto', fontSize:9, fontWeight:700, padding:'2px 6px',
    borderRadius:4, background:'rgba(0,0,0,0.08)', color:'var(--text-muted)',
  },

  typeRow: { display:'grid', gridTemplateColumns:'1fr 1fr', gap:7 },
  typeBtn: {
    display:'flex', alignItems:'center', justifyContent:'center', gap:5,
    padding:'9px 4px', borderRadius:'var(--radius-sm)', border:'1px solid #D5CFC3',
    background:'var(--beige)', color:'var(--text-muted)', fontSize:11, fontWeight:600,
    cursor:'pointer', transition:'all 0.18s',
  },
  typeBtnActive: {
    background:'var(--vino)', border:'1px solid var(--vino-dark)',
    color:'var(--beige)', boxShadow:'var(--shadow-sm)',
  },

  desc: { fontSize:12, color:'var(--text-muted)', lineHeight:1.65 },
  comingSoon: { display:'flex', flexDirection:'column', alignItems:'center', gap:8, padding:'18px 0' },

  runBtn: {
    display:'flex', alignItems:'center', justifyContent:'center', gap:7,
    width:'100%', padding:'11px', borderRadius:'var(--radius-sm)', border:'none',
    background:'var(--vino-gradient)', color:'var(--beige)', fontSize:13, fontWeight:700,
    cursor:'pointer', transition:'filter 0.18s', marginTop:4, boxShadow:'var(--shadow-sm)',
  },
  runBtnDisabled: { filter:'grayscale(60%) opacity(0.75)', cursor:'not-allowed', boxShadow:'none' },

  right: { display:'flex', flexDirection:'column', overflow:'hidden', flex:1, minHeight:0, background:'var(--beige)' },

  // Import panel (for csv and manual modes)
  importPanel: {
    flex:'0 0 auto', maxHeight:'55%', overflow:'auto',
    borderBottom:'1px solid #E5DFD3', background:'var(--beige)',
  },

  termWrap: { flex:'0 0 38%', minHeight:0, overflow:'hidden', display:'flex', flexDirection:'column', borderBottom:'1px solid #2A2A2A', background:'#111' },
  panelHeader: {
    display:'flex', alignItems:'center', justifyContent:'space-between',
    padding:'9px 16px', background:'#1E1E1E', borderBottom:'1px solid #2C2C2C', flexShrink:0,
  },
  panelTitle: { display:'flex', alignItems:'center', fontSize:12, fontWeight:600, color:'#CCC' },
  clearBtn: {
    display:'flex', alignItems:'center', gap:4,
    fontSize:11, color:'#888', background:'rgba(255,255,255,0.04)',
    border:'1px solid #333', cursor:'pointer', padding:'4px 8px',
    borderRadius:4, transition:'background 0.18s',
  },
  termBody: {
    flex:1, padding:'12px 16px', overflowY:'auto', background:'#111',
  },
  cursor: {
    display:'inline-block', width:7, height:13, background:'#90CAF9',
    verticalAlign:'text-bottom', borderRadius:1, animation:'blink 1s step-end infinite',
    marginLeft:3,
  },

  tableWrap: { flex:1, display:'flex', flexDirection:'column', overflow:'hidden', background:'var(--beige)' },
  panelHeaderWhite: {
    display:'flex', alignItems:'center', justifyContent:'space-between',
    padding:'11px 20px', background:'var(--beige-light)', borderBottom:'1px solid #E5DFD3', flexShrink:0,
  },
  panelTitleDark: { display:'flex', alignItems:'center', fontSize:14, fontWeight:700, color:'var(--vino-dark)' },
  countPillDark: {
    display:'flex', alignItems:'center',
    fontSize:11, color:'var(--text-muted)', background:'var(--beige)',
    border:'1px solid #E5DFD3', padding:'4px 12px', borderRadius:20, fontWeight:600,
  },
  reloadBtn: {
    display:'flex', alignItems:'center', gap:4,
    fontSize:11, color:'var(--vino)', background:'rgba(106,27,41,0.05)',
    border:'1px solid rgba(106,27,41,0.18)', cursor:'pointer',
    padding:'4px 10px', borderRadius:20, fontWeight:600, transition:'background 0.18s',
  },
  tableScroll: { flex:1, overflowY:'auto', overflowX:'auto', padding:16 },
  emptyState: { display:'flex', alignItems:'center', justifyContent:'center', gap:8, padding:60, color:'var(--text-muted)', fontSize:14 },

  table: { width:'100%', borderCollapse:'collapse', fontSize:13, background:'var(--beige-light)', borderRadius:8, overflow:'hidden', boxShadow:'var(--shadow-sm)' },
  th: {
    padding:'11px 16px', background:'var(--vino-dim)', color:'var(--vino-dark)',
    fontSize:10, fontWeight:800, textTransform:'uppercase', letterSpacing:'0.9px',
    position:'sticky', top:0, whiteSpace:'nowrap', borderBottom:'2px solid rgba(106,27,41,0.1)', textAlign:'left',
  },
  td:       { padding:'10px 16px', color:'var(--text-dark)', whiteSpace:'nowrap', borderBottom:'1px solid #F0ECE1' },
  nullVal:  { color:'var(--text-muted)', fontStyle:'italic' },
  badgeGrade: {
    display:'inline-block', padding:'3px 10px', borderRadius:6, fontSize:11, fontWeight:700,
    background:'rgba(106,27,41,0.08)', color:'var(--vino)', border:'1px solid rgba(106,27,41,0.15)',
  },
  badgeCurso: {
    display:'inline-block', padding:'3px 10px', borderRadius:6, fontSize:11, fontWeight:700,
    background:'rgba(46,125,50,0.08)', color:'var(--green)', border:'1px solid rgba(46,125,50,0.15)',
  },
}
