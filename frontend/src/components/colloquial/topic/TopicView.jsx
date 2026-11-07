// One topic as a scene: its pictures come first, then the conversation and practice.
import { useRef, useState } from 'react'

import SmallButton from '../../ui/buttons/SmallButton'
import TranslationStrip from '../../ui/text/TranslationStrip'
import Dialogue from './Dialogue'
import { FOCUS } from '../parts/Face'
import Mosaic from './Mosaic'
import Pairs from './Pairs'
import Practice from '../exercises/Practice'
import Sheet from './Sheet'
import SpellingKey from '../parts/SpellingKey'
import WordBank from '../words/WordBank'
import WordGrid from '../words/WordGrid'
import WordPicture from '../words/picture/WordPicture'
import { pictureBoards } from '../../../lib/colloquial/wordPictures'
import { scrollToEl } from '../../../lib/motion/scrollToEl'

function Act({ kicker, title, children }) {
  return (
    <section className="space-y-4">
      <header>
        <p className="eyebrow text-[var(--primary)]">{kicker}</p>
        <h3 className="type-ui font-semibold text-[var(--text)]">{title}</h3>
      </header>
      {children}
    </section>
  )
}

// The first few words, the rest a tap away: the full grid is several screens on a
// phone, and the conversation and practice below it are the topic's main work.
const PREVIEW = 6

function Words({ words }) {
  const [all, setAll] = useState(words.length <= PREVIEW)
  return (
    <>
      <WordGrid words={all ? words : words.slice(0, PREVIEW)} />
      {!all && (
        <button type="button" onClick={() => setAll(true)}
          className={`press w-full py-3 rounded-[var(--radius-md)] border border-[var(--border)] type-ui text-[var(--text-dim)] hover:text-[var(--text)] hover:border-[var(--border-hi)] ${FOCUS}`}>
          Show all {words.length} words
        </button>
      )}
    </>
  )
}

function Scene({ unit, lesson, number, place }) {
  const [open, setOpen] = useState(null)
  // The practice sits several screens down a phone; one tap from the top takes you to it.
  const practice = useRef(null)
  return (
    <article className="space-y-12">
      <div className="space-y-5">
        {/* Headed like the unit page above it, so a topic says its own name, not only the trail. */}
        <header className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="eyebrow text-[var(--text-faint)]">Topic {number}</p>
            <h2 className="type-figure font-semibold text-[var(--text)]">{lesson.title}</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <SmallButton onClick={() => scrollToEl(practice.current, 'top')} className="type-ui px-4 py-2">Practice ↓</SmallButton>
            <WordBank unit={unit} at={number - 1} />
          </div>
        </header>
        <SpellingKey keys={unit.transliteration_key} />
        <Mosaic phrases={lesson.phrases} onOpen={setOpen} />
      </div>
      {/* Phrases first, then the topic's words on their own: a learner needs far
          more single words than any set of phrases can carry. */}
      {lesson.vocabulary?.length > 0 && (
        <Act kicker="Words" title={`${lesson.vocabulary.length} words for this topic`}>
          <Words words={lesson.vocabulary} />
        </Act>
      )}
      {/* Where the words have a drawing (a family tree, a house, a clock), see them on it. */}
      {pictureBoards(lesson.vocabulary ?? []).length > 0 && (
        <div className="max-w-3xl mx-auto">
          <Act kicker="See it" title="On the picture">
            <WordPicture words={lesson.vocabulary} />
          </Act>
        </div>
      )}
      {open !== null && <Sheet phrases={lesson.phrases} at={open} onAt={setOpen} onClose={() => setOpen(null)} place={place} />}

      <div className="space-y-12 lg:space-y-0 lg:grid lg:grid-cols-2 lg:gap-10 lg:items-start">
        <Act kicker="On stage" title="Hear it said">
          <Dialogue lines={lesson.dialogue} />
        </Act>
        <Act kicker="Match" title="Ask and answer">
          <Pairs pairs={lesson.de_book} />
        </Act>
      </div>
      <div ref={practice} className="max-w-3xl mx-auto scroll-mt-[calc(var(--app-header-h,0px)+1rem)]">
        <Act kicker="Your turn" title="Practice">
          <Practice exercises={lesson.exercises} />
        </Act>
      </div>
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden">
        <TranslationStrip pad="px-5 py-5">
          <p className="eyebrow text-[var(--text-faint)] mb-2">Good to know</p>
          <p className="type-body text-[var(--text)] leading-relaxed">{lesson.culture}</p>
        </TranslationStrip>
      </div>
    </article>
  )
}

// One topic of a unit; the panel above owns which unit and topic are open.
export default function TopicView({ unit, at }) {
  return (
    <div className="max-w-3xl lg:max-w-6xl mx-auto">
      <Scene unit={unit} lesson={unit.lessons[at]} number={at + 1}
        place={{ dialect: unit.dialect_key, unit: unit.unit, lesson: unit.lessons[at].lesson }} />
    </div>
  )
}
