// A word topic's example sentences: after its words, the same words said in full, everyday sentences,
// so a learner sees how each is put to use. The phrase topics' tiles and sheet (topic/Mosaic, topic/Sheet),
// so a sentence looks, opens and is heard like a phrase. None for a topic that has none.
import { useState } from 'react'

import Mosaic from '../topic/Mosaic'
import Sheet from '../topic/Sheet'

export default function WordSentences({ sentences = [], narrow = false }) {
  const [open, setOpen] = useState(null)
  if (!sentences.length) return null
  return (
    <section className="space-y-3" aria-labelledby="word-sentences">
      <div>
        <p className="eyebrow text-[var(--text-faint)]">In a sentence</p>
        <h3 id="word-sentences" className="type-ui font-semibold text-[var(--text)]">The words in use</h3>
      </div>
      <Mosaic phrases={sentences} onOpen={setOpen} narrow={narrow} />
      {/* No other-dialect panel: that compares phrase slots, and a sentence is not one. */}
      {open !== null && <Sheet phrases={sentences} at={open} onAt={setOpen} onClose={() => setOpen(null)} noun="sentence" />}
    </section>
  )
}
