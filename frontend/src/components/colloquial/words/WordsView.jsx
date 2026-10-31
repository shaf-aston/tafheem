// One topic's words on their own: see them all as pictures, learn them as cards, warm up by matching, quiz
// yourself, then review what is due. A new way to learn words is a new mode here
// and a component beside this one.
import { useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { onHover, warm } from '../../../lib/api/warm'
import { WORDS_MODULE, wordDrills } from '../../../lib/colloquial/wordPractice'
import { summaryQuery } from '../../../lib/learner/record'
import { readViewParam, writeViewParams } from '../../../lib/nav/tabUrl'
import Segmented from '../../ui/Segmented'
import Practice from '../exercises/Practice'
import WordCards from './WordCards'
import WordGallery from './WordGallery'
import WordMatch from './WordMatch'
import WordPairs from './WordPairs'
import WordReview from './WordReview'
import WordPicture from './picture/WordPicture'
import { pictureBoards } from '../../../lib/colloquial/wordPictures'

const MODES = [{ id: 'browse', label: 'Browse' }, { id: 'cards', label: 'Cards' }, { id: 'match', label: 'Match' }, { id: 'quiz', label: 'Quiz' }, { id: 'review', label: 'Review' }]
// Only where the words have a drawing to match (the body, countries): lib/colloquial/wordPictures.js.
const PICTURE = { id: 'picture', label: 'Picture' }
const WIDE = new Set(['browse', 'review'])
const MODE_IDS = [...MODES, PICTURE].map((m) => m.id)

export default function WordsView({ unit, at }) {
  const lesson = unit.lessons[at]
  const words = lesson.vocabulary
  // The mode rides on the address (?words=cards in a shared link), so a reload or a link keeps it.
  const [mode, setModeNow] = useState(() => readViewParam('words', MODE_IDS) ?? 'browse')
  const setMode = (next) => { setModeNow(next); writeViewParams({ words: next === 'browse' ? '' : next }) }
  const dialect = unit.dialect_key
  // Review plans from the words' record: fetched ahead when the topic opens, and again
  // on reaching for the modes (only if an answer has made it old), so it opens at once.
  const client = useQueryClient()
  const record = summaryQuery(WORDS_MODULE)
  useEffect(() => { warm(client, summaryQuery(WORDS_MODULE)) }, [client])
  const modes = useMemo(() => (pictureBoards(words).length ? [...MODES.slice(0, 3), PICTURE, ...MODES.slice(3)] : MODES), [words])
  // A topic with no drawing has no Picture mode: a link asking for one opens on Browse.
  const shown = modes.some((m) => m.id === mode) ? mode : 'browse'
  const drills = useMemo(() => wordDrills(words, `${unit.unit}.${lesson.lesson}`, { dialect }), [words, unit.unit, lesson.lesson, dialect])

  // Browse and Review lay many tiles side by side; the rest are one card wide.
  return (
    <article className={`${WIDE.has(shown) ? 'max-w-5xl' : 'max-w-xl'} mx-auto space-y-6`}>
      {/* The topic's title is already on the trail above, one step before Words. */}
      {/* One width in every mode, so the modes stay put when Review widens the page. */}
      <header className="w-full max-w-xl mx-auto flex flex-wrap items-end justify-between gap-3">
        {/* A heading, so the word groups under it (h4) sit one level down from the tab's h2. */}
        <h3 className="eyebrow text-[var(--text-faint)]">Topic {at + 1} · {words.length} words</h3>
        <div {...onHover(client, record)}>
          <Segmented label="How to learn the words" accent="var(--primary)" value={shown} onChange={setMode} options={modes} />
        </div>
      </header>
      {/* Keyed by the mode, so each one rises in as the rest of the tab's views do. */}
      <div key={shown} className="rise-in">
        {shown === 'browse' && (lesson.pairs ? <WordPairs words={words} pairs={lesson.pairs} /> : <WordGallery words={words} />)}
        {shown === 'cards' && <WordCards words={words} />}
        {shown === 'match' && <WordMatch words={words} />}
        {shown === 'picture' && <WordPicture words={words} />}
        {shown === 'quiz' && <Practice exercises={drills} />}
        {shown === 'review' && <WordReview words={words} dialect={dialect} />}
      </div>
    </article>
  )
}
