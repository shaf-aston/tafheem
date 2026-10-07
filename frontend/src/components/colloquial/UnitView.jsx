// One topic as a scene: its pictures come first, then the conversation and practice.
import { useState } from 'react'

import TranslationStrip from '../ui/TranslationStrip'
import Dialogue from './Dialogue'
import Mosaic from './Mosaic'
import Pairs from './Pairs'
import Practice from './Practice'
import Sheet from './Sheet'
import WordBank from './WordBank'

function Act({ kicker, title, children }) {
  return (
    <section className="space-y-4">
      <header>
        <p className="type-micro uppercase tracking-[0.18em] text-[var(--primary)]">{kicker}</p>
        <h3 className="type-ui font-semibold text-[var(--text)]">{title}</h3>
      </header>
      {children}
    </section>
  )
}

function Scene({ unit, lesson, number, place }) {
  const [open, setOpen] = useState(null)
  return (
    <article className="space-y-12">
      <div className="space-y-5">
        {/* The topic's title is the last step of the trail just above, so it is not said again here. */}
        <header className="flex flex-wrap items-end justify-between gap-3">
          <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">Topic {number}</p>
          <WordBank unit={unit} at={number - 1} />
        </header>
        <Mosaic phrases={lesson.phrases} onOpen={setOpen} />
      </div>
      {open !== null && <Sheet phrases={lesson.phrases} at={open} onAt={setOpen} onClose={() => setOpen(null)} place={place} />}

      <div className="space-y-12 lg:space-y-0 lg:grid lg:grid-cols-2 lg:gap-10 lg:items-start">
        <Act kicker="On stage" title="Hear it said">
          <Dialogue lines={lesson.dialogue} />
        </Act>
        <Act kicker="Match" title="Ask and answer">
          <Pairs pairs={lesson.de_book} />
        </Act>
      </div>
      <div className="max-w-3xl mx-auto">
        <Act kicker="Your turn" title="Practice">
          <Practice exercises={lesson.exercises} />
        </Act>
      </div>
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden">
        <TranslationStrip pad="px-5 py-5">
          <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)] mb-2">Good to know</p>
          <p className="type-body text-[var(--text)] leading-relaxed">{lesson.culture}</p>
        </TranslationStrip>
      </div>
    </article>
  )
}

// One topic of a unit; the panel above owns which unit and topic are open.
export default function UnitView({ unit, at }) {
  return (
    <div className="max-w-3xl lg:max-w-6xl mx-auto">
      <Scene unit={unit} lesson={unit.lessons[at]} number={at + 1}
        place={{ dialect: unit.dialect_key, unit: unit.unit, lesson: unit.lessons[at].lesson }} />
    </div>
  )
}
