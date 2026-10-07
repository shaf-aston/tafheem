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

// Repeats across topics show once: a word by its meaning's id, a phrase by its Arabic.
const keyOf = (r) => r.id ?? r.arabic
function unique(rows) {
  const seen = new Set()
  return rows.filter((r) => r && !seen.has(keyOf(r)) && seen.add(keyOf(r)))
}

// A phrase and the reply that goes with it are both worth learning.
const phrasesOf = (lessons) => unique(lessons.filter((l) => l.written).flatMap((l) => l.phrases.flatMap((p) => [p, p.reply])))
const wordsOf = (lessons) => unique(lessons.filter((l) => l.written).flatMap((l) => l.vocabulary ?? []))

// Rows under their category heading, in the order written; uncategorised rows sit under none.
function grouped(rows) {
  const by = new Map()
  for (const r of rows) {
    const key = r.category ?? ''
    by.set(key, [...(by.get(key) ?? []), r])
  }
  return [...by]
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
      <div className="overflow-y-auto px-5 pb-5 space-y-4">
        {grouped(rows).map(([category, group]) => (
          <section key={category}>
            {category && <h3 className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)] pt-2">{category}</h3>}
            <ul className="grid sm:grid-cols-2 sm:gap-x-8">
              {group.map((r) => (
                <li key={keyOf(r)} className="flex items-baseline justify-between gap-4 py-2.5 border-b border-[var(--border)]">
                  <span className="min-w-0">
                    <span className="type-body text-[var(--text)]">{r.english}</span>
                    <Spelling className="block">{r.transliteration}</Spelling>
                  </span>
                  <span className="shrink-0 flex items-center gap-2">
                    <SpeakButton text={r.arabic} />
                    <ArabicText as="span" size="base" className="text-[var(--text)]">{r.arabic}</ArabicText>
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </BottomSheet>
  )
}

// `at` is the open topic; with none (the unit screen) the bank is the whole unit.
export default function WordBank({ unit, at = null }) {
  const [open, setOpen] = useState(false)
  const [whole, setWhole] = useState(at === null)
  const topic = at === null ? null : unit.lessons[at]
  const lessons = whole || !topic ? unit.lessons : [topic]
  const words = wordsOf(lessons)
  const [show, setShow] = useState('words')
  const rows = show === 'words' && words.length > 0 ? words : phrasesOf(lessons)
  const scope = (words.length > 0 || topic) && (
    <div className="space-y-2">
      {words.length > 0 && (
        <Segmented label="Word bank kind" accent="var(--primary)" value={show} onChange={setShow}
          options={[{ id: 'words', label: 'Words' }, { id: 'phrases', label: 'Phrases' }]} />
      )}
      {topic && (
        <Segmented label="Word bank scope" accent="var(--primary)" value={whole ? 'unit' : 'topic'}
          onChange={(v) => setWhole(v === 'unit')}
          options={[{ id: 'topic', label: 'This topic' }, { id: 'unit', label: 'Whole unit' }]} />
      )}
    </div>
  )
  return (
    <>
      <SmallButton onClick={() => setOpen(true)} className="inline-flex items-center gap-2 type-ui px-4 py-2">
        <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5zM12 6.5v13" />
        </svg>
        Word bank
      </SmallButton>
      {open && <Bank rows={rows} onClose={() => setOpen(false)} scope={scope} title={whole || !topic ? unit.title : topic.title} />}
    </>
  )
}
