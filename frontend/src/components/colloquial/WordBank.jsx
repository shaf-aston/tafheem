// Every word and phrase of a topic or a whole unit as a plain list, for raw vocab learning.
// Built from the unit already loaded, so it adds no request.
import { useState } from 'react'

import ArabicText from '../ui/ArabicText'
import BottomSheet from '../ui/BottomSheet'
import CloseButton from '../ui/CloseButton'
import Segmented from '../ui/Segmented'
import SmallButton from '../ui/SmallButton'
import SpeakButton from '../ui/SpeakButton'
import { FOCUS } from './Face'
import Spelling from './Spelling'

// A phrase and the reply that goes with it are both worth learning; repeats across topics show once.
function rowsOf(lessons) {
  const seen = new Set()
  return lessons.filter((l) => l.written).flatMap((l) => l.phrases.flatMap((p) => [p, p.reply])).filter((r) => {
    if (!r || seen.has(r.arabic)) return false
    seen.add(r.arabic)
    return true
  })
}

function Bank({ rows, onClose, scope, title }) {
  return (
    <BottomSheet label={title} onClose={onClose} className="max-h-[var(--sheet-tall)] flex flex-col">
      <header className="flex items-center justify-between gap-3 px-5 pt-4 pb-3">
        <div className="min-w-0">
          <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">Word bank</p>
          <h2 className="type-ui font-semibold text-[var(--text)] truncate">{title}</h2>
        </div>
        <CloseButton onClick={onClose} className={`shrink-0 ${FOCUS}`} />
      </header>
      {scope && <div className="px-5 pb-3">{scope}</div>}
      <ul className="overflow-y-auto px-5 pb-5 grid sm:grid-cols-2 sm:gap-x-8">
        {rows.map((r) => (
          <li key={r.arabic} className="flex items-baseline justify-between gap-4 py-2.5 border-b border-[var(--border)]">
            <span className="min-w-0">
              <span className="type-small text-[var(--text)]">{r.english}</span>
              <Spelling className="block">{r.transliteration}</Spelling>
            </span>
            <span className="shrink-0 flex items-center gap-2">
              <SpeakButton text={r.arabic} />
              <ArabicText as="span" size="base" className="text-[var(--text)]">{r.arabic}</ArabicText>
            </span>
          </li>
        ))}
      </ul>
    </BottomSheet>
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
