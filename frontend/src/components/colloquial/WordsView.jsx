// One topic's words on their own: learn them as cards, warm up by matching, quiz
// yourself, then review what is due. A new way to learn words is a new mode here
// and a component beside this one.
import { useMemo, useState } from 'react'

import { wordDrills } from '../../lib/wordDrills'
import Segmented from '../ui/Segmented'
import Practice from './Practice'
import WordCards from './WordCards'
import WordMatch from './WordMatch'
import WordReview from './WordReview'

const MODES = [{ id: 'cards', label: 'Cards' }, { id: 'match', label: 'Match' }, { id: 'quiz', label: 'Quiz' }, { id: 'review', label: 'Review' }]

export default function WordsView({ unit, at }) {
  const lesson = unit.lessons[at]
  const words = lesson.vocabulary
  const [mode, setMode] = useState('cards')
  const dialect = unit.dialect_key
  const drills = useMemo(() => wordDrills(words, `${unit.unit}.${lesson.lesson}`, { dialect }), [words, unit.unit, lesson.lesson, dialect])

  return (
    <article className="max-w-xl mx-auto space-y-6">
      {/* The topic's title is already on the trail above, one step before Words. */}
      <header className="flex flex-wrap items-end justify-between gap-3">
        <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">Topic {at + 1} · {words.length} words</p>
        <Segmented label="How to learn the words" accent="var(--primary)" value={mode} onChange={setMode} options={MODES} />
      </header>
      {mode === 'cards' && <WordCards words={words} />}
      {mode === 'match' && <WordMatch words={words} />}
      {mode === 'quiz' && <Practice exercises={drills} />}
      {mode === 'review' && <WordReview words={words} dialect={dialect} />}
    </article>
  )
}
