// A topic of opposites, browsed two by two: each word beside its other (fast ↔ slow),
// tapped to hear it. "Hide one side" covers the right-hand words, so the learner
// says the opposite before tapping to see it. The pairs come from the spine
// (`"pairs": true`), in its order.
import { useState } from 'react'

import { speak } from '../../../lib/speech/speak'
import { useAccent } from '../../../lib/theme/accent'
import ArabicText from '../../ui/ArabicText'
import Segmented from '../../ui/Segmented'
import { FOCUS } from '../parts/Face'
import PhrasePicture from '../parts/PhrasePicture'
import Spelling from '../parts/Spelling'

const VIEWS = [{ id: 'both', label: 'Show both' }, { id: 'hide', label: 'Hide one side' }]

function Side({ word, covered, onReveal, of }) {
  const accent = useAccent()
  if (covered) {
    return (
      <button type="button" onClick={onReveal} aria-label={`Show the opposite of ${of}`}
        className={`h-full min-h-28 w-full rounded-[var(--radius-md)] border border-dashed border-[var(--border-hi)]
          type-small text-[var(--text-faint)] hover:text-[var(--text-dim)] ${FOCUS}`}>
        Say it, then tap
      </button>
    )
  }
  return (
    <button type="button" onClick={() => speak(word.arabic, { accent }).catch(() => {})}
      aria-label={`${word.english}: hear it`}
      className={`h-full min-h-28 w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-3
        flex flex-col items-center justify-center gap-1 text-center hover:border-[var(--border-hi)] ${FOCUS}`}>
      {word.image && <PhrasePicture phrase={word} alt="" className="size-12 rounded-[var(--radius-sm)]" />}
      <ArabicText as="span" size="base" className="text-[var(--text)]">{word.arabic}</ArabicText>
      <Spelling className="block">{word.transliteration}</Spelling>
      <span className="type-small text-[var(--text-dim)]">{word.english}</span>
    </button>
  )
}

export default function WordPairs({ words, pairs }) {
  const [view, setView] = useState('both')
  const [shown, setShown] = useState(() => new Set())
  const byId = Object.fromEntries(words.map((w) => [w.id, w]))
  const rows = pairs.map(([a, b]) => [byId[a], byId[b]]).filter(([a, b]) => a && b)
  const hiding = view === 'hide'
  const pick = (next) => { setView(next); setShown(new Set()) }
  return (
    <div className="max-w-xl mx-auto space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="type-small text-[var(--text-dim)]">{rows.length} pairs of opposites</p>
        <Segmented label="Both sides or one" accent="var(--primary)" value={view} onChange={pick} compact options={VIEWS} />
      </div>
      <ul className="space-y-2">
        {rows.map(([a, b]) => {
          const reveal = () => setShown((s) => new Set(s).add(b.id))
          return (
            <li key={a.id} className="grid grid-cols-[1fr_auto_1fr] items-stretch gap-2">
              <Side word={a} />
              <span aria-hidden="true" className="self-center type-body text-[var(--text-faint)]">↔</span>
              <Side word={b} covered={hiding && !shown.has(b.id)} onReveal={reveal} of={a.english} />
            </li>
          )
        })}
      </ul>
    </div>
  )
}
