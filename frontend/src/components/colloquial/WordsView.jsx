// One topic's words on their own: learn them as cards, then quiz yourself. A new way to
// learn words is a new mode here and a component beside this one.
import { useMemo, useState } from 'react'

import { wordDrills } from '../../lib/wordDrills'
import Segmented from '../ui/Segmented'
import Practice from './Practice'
import WordCards from './WordCards'

const MODES = [{ id: 'cards', label: 'Cards' }, { id: 'quiz', label: 'Quiz' }]

export default function WordsView({ unit, at }) {
  const lesson = unit.lessons[at]
  const words = lesson.vocabulary
  const [mode, setMode] = useState('cards')
  const drills = useMemo(() => wordDrills(words, `${unit.unit}.${lesson.lesson}`), [words, unit.unit, lesson.lesson])

  return (
    <article className="max-w-xl mx-auto space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">Topic {at + 1} · {words.length} words</p>
          <h2 className="type-figure font-semibold text-[var(--text)]">{lesson.title}</h2>
        </div>
        <Segmented label="How to learn the words" accent="var(--primary)" value={mode} onChange={setMode} options={MODES} />
      </header>
      {mode === 'cards' ? <WordCards words={words} /> : <Practice exercises={drills} />}
    </article>
  )
}
