// A topic's words laid out like a talk topic's phrases: a picture mosaic under
// each heading, any tile opening the sheet that steps through every word.
import { useState } from 'react'

import { grouped } from '../../../lib/colloquial/wordGroups'
import Mosaic from '../topic/Mosaic'
import Sheet from '../topic/Sheet'

export default function WordGallery({ words }) {
  const [open, setOpen] = useState(null)
  const groups = grouped(words)
  // Grouping can reorder words, so the sheet steps through them in the order shown.
  const shown = groups.flatMap(([, group]) => group)
  // Where each heading's tiles start in that order.
  const starts = groups.map((_, g) => groups.slice(0, g).reduce((n, [, group]) => n + group.length, 0))
  return (
    <div className="space-y-6">
      {groups.map(([category, group], g) => (
        <section key={category} className="space-y-2">
          {category && <h4 className="eyebrow text-[var(--text-faint)]">{category}</h4>}
          <Mosaic phrases={group} start={starts[g]} onOpen={setOpen} />
        </section>
      ))}
      {open !== null && <Sheet phrases={shown} at={open} onAt={setOpen} onClose={() => setOpen(null)} noun="word" />}
    </div>
  )
}
