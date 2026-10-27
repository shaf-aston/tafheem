// One topic's words on their own: learn them as cards, warm up by matching, quiz
// yourself, then review what is due. A new way to learn words is a new mode here
// and a component beside this one.
import { useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { onHover, warm } from '../../../lib/api/warm'
import { WORDS_MODULE, wordDrills } from '../../../lib/colloquial/wordPractice'
import { summaryQuery } from '../../../lib/learner/record'
import Segmented from '../../ui/inputs/Segmented'
import Practice from '../exercises/Practice'
import WordCards from './WordCards'
import WordMatch from './WordMatch'
import WordReview from './WordReview'

const MODES = [{ id: 'cards', label: 'Cards' }, { id: 'match', label: 'Match' }, { id: 'quiz', label: 'Quiz' }, { id: 'review', label: 'Review' }]

export default function WordsView({ unit, at }) {
  const lesson = unit.lessons[at]
  const words = lesson.vocabulary
  const [mode, setMode] = useState('cards')
  const dialect = unit.dialect_key
  // Review plans from the words' record: fetched ahead when the topic opens, and again
  // on reaching for the modes (only if an answer has made it old), so it opens at once.
  const client = useQueryClient()
  const record = summaryQuery(WORDS_MODULE)
  useEffect(() => { warm(client, summaryQuery(WORDS_MODULE)) }, [client])
  const drills = useMemo(() => wordDrills(words, `${unit.unit}.${lesson.lesson}`, { dialect }), [words, unit.unit, lesson.lesson, dialect])

  return (
    <article className={`${mode === 'review' ? 'max-w-5xl' : 'max-w-xl'} mx-auto space-y-6`}>
      {/* The topic's title is already on the trail above, one step before Words. */}
      {/* One width in every mode, so the modes stay put when Review widens the page. */}
      <header className="w-full max-w-xl mx-auto flex flex-wrap items-end justify-between gap-3">
        <p className="eyebrow text-[var(--text-faint)]">Topic {at + 1} · {words.length} words</p>
        <div {...onHover(client, record)}>
          <Segmented label="How to learn the words" accent="var(--primary)" value={mode} onChange={setMode} options={MODES} />
        </div>
      </header>
      {/* Keyed by the mode, so each one rises in as the rest of the tab's views do. */}
      <div key={mode} className="rise-in">
        {mode === 'cards' && <WordCards words={words} />}
        {mode === 'match' && <WordMatch words={words} />}
        {mode === 'quiz' && <Practice exercises={drills} />}
        {mode === 'review' && <WordReview words={words} dialect={dialect} />}
      </div>
    </article>
  )
}
