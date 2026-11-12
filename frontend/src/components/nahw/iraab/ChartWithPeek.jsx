import { useRef, useState } from 'react'

import { bareForm } from '../../../lib/text/arabicText'
import TarkeebFigure from '../../grammar/tarkeeb/TarkeebFigure'
import WordPeek from '../WordPeek'

// The written word a chart word is: the analysis lists the words on the page in
// order, so the nth is the one, unless the two spellings disagree (a word the
// parser split differently), when the first with the same letters is.
function nthWord(list, nth, text, key) {
  const same = (item) => item && bareForm(item[key]) === bareForm(text)
  return same(list?.[nth]) ? list[nth] : list?.find(same)
}

// The chart, with a tapped word answered in a small panel under it, in place.
export default function ChartWithPeek({ data, view, glosses, onMore, onLookup, foot }) {
  const [peek, setPeek] = useState(null)
  const frame = useRef(null)
  const glossOf = (nth, text) => nthWord(glosses, nth, text, 'arabic')?.english
  const open = (text, nth, el) => {
    const word = nthWord(data.words, nth, text, 'word')
    if (!word) return onLookup?.(text)
    const box = frame.current.getBoundingClientRect()
    const at = el.getBoundingClientRect()
    // kept inside the frame, so the panel never hangs off a phone's edge
    const half = Math.min(144, box.width / 2)
    const x = Math.min(Math.max(at.left + at.width / 2 - box.left, half), box.width - half)
    setPeek({ word, english: glossOf(nth, text), text, at: { x, y: at.bottom - box.top + 6 } })
  }
  return (
    <div ref={frame} className="relative">
      <TarkeebFigure tarkeeb={data.tree} view={view} onWord={open} glossOf={glosses && glossOf}
        foot={foot} />
      {peek && (
        <WordPeek {...peek} onClose={() => setPeek(null)}
          onMore={() => { onMore(peek.word); setPeek(null) }}
          onLookup={() => onLookup?.(peek.text)} />
      )}
    </div>
  )
}
