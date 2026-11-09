// Every word and phrase of a topic or a whole unit as a plain list, for raw vocab learning.
// Built from the unit already loaded, so it adds no request.
import { useEffect, useRef, useState } from 'react'

import ArabicText from '../ui/ArabicText'
import Segmented from '../ui/Segmented'
import SmallButton from '../ui/SmallButton'
import { FOCUS } from './Face'
import Spelling from './Spelling'

// A phrase and the reply that goes with it are both worth learning; repeats across topics show once.
function rowsOf(lessons) {
  const seen = new Set()
  return lessons.flatMap((l) => l.phrases.flatMap((p) => [p, p.reply])).filter((r) => {
    if (!r || seen.has(r.arabic)) return false
    seen.add(r.arabic)
    return true
  })
}

function Bank({ rows, onClose, scope, title }) {
  const closeRef = useRef(null)
  useEffect(() => {
    const opener = document.activeElement
    closeRef.current?.focus()
    const { overflow } = document.body.style
    document.body.style.overflow = 'hidden'
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
      opener?.focus?.()
    }
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-[var(--layer-overlay)] flex items-end sm:items-center justify-center"
      style={{ background: 'color-mix(in srgb, var(--bg) 82%, transparent)' }}
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full sm:max-w-lg max-h-[85dvh] flex flex-col bg-[var(--surface)] border border-[var(--border-hi)]
          rounded-t-[var(--radius-md)] sm:rounded-[var(--radius-md)] shadow-[var(--shadow-pop)]"
      >
        <header className="flex items-center justify-between gap-3 px-5 pt-4 pb-3">
          <div className="min-w-0">
            <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">Word bank</p>
            <h2 className="type-ui font-semibold text-[var(--text)] truncate">{title}</h2>
          </div>
          <button ref={closeRef} type="button" onClick={onClose} aria-label="Close"
            className={`press shrink-0 w-9 h-9 grid place-items-center rounded-full border border-[var(--border-hi)] text-[var(--text)] ${FOCUS}`}>
            <span aria-hidden="true">✕</span>
          </button>
        </header>
        {scope && <div className="px-5 pb-3">{scope}</div>}
        <ul className="overflow-y-auto px-5 pb-5 divide-y divide-[var(--border)]">
          {rows.map((r) => (
            <li key={r.arabic} className="flex items-baseline justify-between gap-4 py-2.5">
              <span className="min-w-0">
                <span className="type-small text-[var(--text)]">{r.english}</span>
                <Spelling className="block">{r.transliteration}</Spelling>
              </span>
              <ArabicText as="span" size="base" className="shrink-0 text-[var(--text)]">{r.arabic}</ArabicText>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

// `at` is the open topic; with none (the unit screen) the bank is the whole unit.
export default function WordBank({ unit, at = null }) {
  const [open, setOpen] = useState(false)
  const [whole, setWhole] = useState(at === null)
  const topic = at === null ? null : unit.lessons[at]
  const rows = rowsOf(whole || !topic ? unit.lessons : [topic])
  const scope = topic && (
    <Segmented label="Word bank scope" accent="var(--primary)" value={whole ? 'unit' : 'topic'}
      onChange={(v) => setWhole(v === 'unit')}
      options={[{ id: 'topic', label: 'This topic' }, { id: 'unit', label: 'Whole unit' }]} />
  )
  return (
    <>
      <SmallButton onClick={() => setOpen(true)}>Word bank</SmallButton>
      {open && <Bank rows={rows} onClose={() => setOpen(false)} scope={scope} title={whole || !topic ? unit.title : topic.title} />}
    </>
  )
}
