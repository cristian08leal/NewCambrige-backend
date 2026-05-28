// =============================================================================
// components/PersonTypeSelector.jsx — Selector Estudiante / Docente
// =============================================================================
import { MdSchool, MdPeople } from 'react-icons/md'
import { useImport } from './ImportContext'

export default function PersonTypeSelector({ disabled }) {
  const { personType, setPersonType } = useImport()

  return (
    <div style={styles.wrap}>
      <div style={styles.label}>
        <MdPeople size={13} style={{ opacity: 0.7, marginRight: 5 }} />
        TIPO DE PERSONA
      </div>
      <div style={styles.row}>
        <button
          style={{
            ...styles.btn,
            ...(personType === 'estudiante' ? styles.btnActive : {})
          }}
          onClick={() => setPersonType('estudiante')}
          disabled={disabled}
        >
          <MdSchool size={14} />
          Estudiante
        </button>
        <button
          style={{
            ...styles.btn,
            ...(personType === 'docente' ? styles.btnActive : {})
          }}
          onClick={() => setPersonType('docente')}
          disabled={disabled}
        >
          <MdPeople size={14} />
          Docente
        </button>
      </div>
    </div>
  )
}

const styles = {
  wrap: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  label: {
    display: 'flex',
    alignItems: 'center',
    fontSize: 10,
    fontWeight: 800,
    textTransform: 'uppercase',
    letterSpacing: '1.2px',
    color: 'var(--vino)',
    paddingBottom: 8,
    borderBottom: '2px solid var(--vino)',
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 7,
  },
  btn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: '10px 4px',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid #D5CFC3',
    background: 'var(--beige)',
    color: 'var(--text-muted)',
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  btnActive: {
    background: 'var(--vino)',
    border: '1px solid var(--vino-dark)',
    color: 'var(--beige)',
    boxShadow: 'var(--shadow-sm)',
  }
}
