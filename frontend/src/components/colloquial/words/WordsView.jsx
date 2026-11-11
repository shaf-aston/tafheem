// One topic's words on their own: see them all as pictures, learn them as cards, warm up by matching, quiz
// yourself, then review what is due. A new way to learn words is a new mode here
// and a component beside this one.
import { useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { onHover, warm } from '../../../lib/api/warm'
import { WORDS_MODULE, wordDrills } from '../../../lib/colloquial/wordPractice'
import { summaryQuery } from '../../../lib/learner/record'
import { scrollToTop } from '../../../lib/motion/scrollToEl'
import { readViewParam, writeViewParams } from '../../../lib/nav/tabUrl'
import Segmented from '../../ui/inputs/Segmented'
import Practice from '../exercises/Practice'
import SpellingKey from '../parts/SpellingKey'
import WordCards from './WordCards'
import WordGallery from './WordGallery'
import WordMatch from './WordMatch'
import WordPairs from './WordPairs'
import WordReview from './WordReview'
import WordPicture from './picture/WordPicture'
import { pictureBoards } from '../../../lib/colloquial/wordPictures'

const MODES = [{ id: 'browse', label: 'Browse' }, { id: 'cards', label: 'Cards' }, { id: 'match', label: 'Match' }, { id: 'quiz', label: 'Quiz' }, { id: 'review', label: 'Review' }]
const WIDE = new Set(['browse', 'review'])
// 'picture' was a mode of its own once; the drawing is in Browse now, so an old link to it opens there.
const MODE_IDS = [...MODES.map((m) => m.id), 'picture']

export default function WordsView({ unit, at }) {
  const lesson = unit.lessons[at]
  const words = lesson.vocabulary
  // The mode rides on the address (?words=cards in a shared link), so a reload or a link keeps it.
  const [mode, setModeNow] = useState(() => readViewParam('words', MODE_IDS) ?? 'browse')
  // A mode picked here rises in, as an answer to the tap; the first arrives with its screen (ui/display/Screen.jsx).
  const [picked, setPicked] = useState(false)
  const setMode = (next) => { setModeNow(next); setPicked(true); writeViewParams({ words: next === 'browse' ? '' : next }) }
  const dialect = unit.dialect_key
  // Review plans from the words' record: fetched ahead when the topic opens, and again
  // on reaching for the modes (only if an answer has made it old), so it opens at once.
  const client = useQueryClient()
  const record = summaryQuery(WORDS_MODULE)
  useEffect(() => { warm(client, summaryQuery(WORDS_MODULE)) }, [client])
  const shown = mode === 'picture' ? 'browse' : mode
  // Where the words have a drawing (the body, a house, the countries: lib/colloquial/wordPictures.js) Browse
  // opens with it, so they are met on it as well as in a list.
  const drawn = useMemo(() => pictureBoards(words).length > 0, [words])
  const drills = useMemo(() => wordDrills(words, `${unit.unit}.${lesson.lesson}`, { dialect }), [words, unit.unit, lesson.lesson, dialect])

  if (!words.length) return <p className="type-small text-[var(--text-faint)] text-center py-12">This topic has no words yet.</p>

  // Browse and Review lay many tiles side by side; the rest are one card wide.
  return (
    <article className={`${shown === 'browse' && drawn ? 'max-w-6xl' : WIDE.has(shown) ? 'max-w-5xl' : 'max-w-xl'} mx-auto space-y-6`}>
      {/* One width in every mode, so the modes stay put when Review widens the page. */}
      {/* Headed like a phrase topic (topic/TopicView.jsx), so every topic says its own name, not only the trail. */}
      <header className={`w-full space-y-4 ${shown === 'browse' && drawn ? '' : 'max-w-xl mx-auto'}`}>
        <div>
          <p className="eyebrow text-[var(--text-faint)]">Topic {at + 1} · {words.length} words</p>
          <h2 className="type-figure font-semibold text-[var(--text)]">{lesson.title}</h2>
        </div>
        <div {...onHover(client, record)}>
          <Segmented label="How to learn the words" accent="var(--primary)" value={shown} onChange={setMode} options={MODES} />
        </div>
      </header>
      {/* Over the words, not the quiz; beside a drawing it heads the words' own column instead. */}
      {shown !== 'quiz' && !(shown === 'browse' && drawn) && <div className="w-full max-w-xl mx-auto"><SpellingKey keys={unit.transliteration_key} /></div>}
      {/* Keyed by the mode, so a newly picked one rises in. */}
      <div key={shown} className={picked ? 'rise-in' : undefined}>
        {shown === 'browse' && (drawn
          ? (
            // The drawing, with its picker and question, beside the words on a wide screen (all held in view as the words scroll past); over them on a phone.
            <WordPicture words={words}>
              <SpellingKey keys={unit.transliteration_key} />
              {lesson.pairs ? <WordPairs words={words} pairs={lesson.pairs} /> : <WordGallery words={words} narrow />}
            </WordPicture>
          )
          : (lesson.pairs ? <WordPairs words={words} pairs={lesson.pairs} /> : <WordGallery words={words} />))}
        {shown === 'cards' && <WordCards words={words} />}
        {shown === 'match' && <WordMatch words={words} />}
        {shown === 'quiz' && <Practice exercises={drills} />}
        {shown === 'review' && <WordReview words={words} dialect={dialect} />}
      </div>
      {/* Looking is the first step, not the last: the page ends by offering the next one, as a topic ends with its next topic. */}
      {shown === 'browse' && (
        <button type="button" onClick={() => { setMode('cards'); scrollToTop() }}
          className="press block w-full max-w-xl mx-auto py-4 rounded-[var(--radius-md)] border border-[var(--border-hi)] type-ui font-semibold text-[var(--primary)] hover:bg-[var(--surface-hi)] focus-visible:outline-2 focus-visible:outline-[var(--primary)]">
          Now learn them as cards →
        </button>
      )}
    </article>
  )
}
