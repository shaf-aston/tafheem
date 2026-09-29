// One topic as a scene: its pictures come first, then the conversation and practice.
import { useState } from 'react'

import TranslationStrip from '../ui/TranslationStrip'
import Dialogue from './Dialogue'
import Mosaic from './Mosaic'
import Pairs from './Pairs'
import Practice from './Practice'
import Sheet from './Sheet'

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

function Scene({ lesson, number }) {
  const [open, setOpen] = useState(null)
  return (
    <article className="space-y-12">
      <header className="space-y-1">
        <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">Scene {number}</p>
        <h2 className="type-figure font-semibold text-[var(--text)]">{lesson.title}</h2>
        <p className="type-small text-[var(--text-dim)]">Press a picture to look closer.</p>
      </header>

      <Mosaic phrases={lesson.phrases} onOpen={setOpen} />
      {open !== null && <Sheet phrases={lesson.phrases} at={open} onAt={setOpen} onClose={() => setOpen(null)} />}

      <Act kicker="On stage" title="Hear it said">
        <Dialogue lines={lesson.dialogue} />
      </Act>
      <Act kicker="Match" title="Ask and answer">
        <Pairs pairs={lesson.de_book} />
      </Act>
      <Act kicker="Your turn" title="Practice">
        <Practice exercises={lesson.exercises} />
      </Act>
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
    <div className="max-w-3xl mx-auto">
      <Scene lesson={unit.lessons[at]} number={at + 1} />
    </div>
  )
}
