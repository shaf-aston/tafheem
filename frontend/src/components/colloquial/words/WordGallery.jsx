// A topic's words laid out like a talk topic's phrases: a picture mosaic under
// each heading, any tile opening the sheet that steps through every word.
// Under a heading, the words with a picture come first as the mosaic, and the
// ones with none follow as short word tiles, so no big tile is left empty.
import { useState } from 'react'

import { grouped } from '../../../lib/colloquial/wordGroups'
import Mosaic from '../topic/Mosaic'
import Sheet from '../topic/Sheet'

// Each heading's words split into its pictured run and its plain run, in that order.
const runs = (words) => grouped(words).map(([category, group]) => [
  category,
  [group.filter((w) => w.image), group.filter((w) => !w.image)].filter((run) => run.length),
])

export default function WordGallery({ words }) {
  const [open, setOpen] = useState(null)
  const sections = runs(words)
  // The sheet steps through the words in the order they are shown.
  const shown = sections.flatMap(([, parts]) => parts.flat())
  // Where each run's tiles start in that order.
  const sizes = sections.flatMap(([, parts]) => parts.map((run) => run.length))
  const starts = sizes.map((_, at) => sizes.slice(0, at).reduce((n, size) => n + size, 0))
  const firstRun = sections.map((_, s) => sections.slice(0, s).reduce((n, [, parts]) => n + parts.length, 0))
  return (
    <div className="space-y-6">
      {sections.map(([category, parts], s) => (
        <section key={category} className="space-y-2">
          {category && <h4 className="eyebrow text-[var(--text-faint)]">{category}</h4>}
          {parts.map((run, p) => {
            const at = starts[firstRun[s] + p]
            return <Mosaic key={at} phrases={run} start={at} onOpen={setOpen} />
          })}
        </section>
      ))}
      {open !== null && <Sheet phrases={shown} at={open} onAt={setOpen} onClose={() => setOpen(null)} noun="word" />}
    </div>
  )
}
