import { useMemo, useRef, useState } from 'react'

import { align, layout } from '../../../lib/nahw/tarkeebLayout'
import TarkeebFigure from '../../grammar/tarkeeb/TarkeebFigure'
import WordPeek from '../WordPeek'

// The chart, with a tapped word answered in a small panel under it, in place.
export default function ChartWithPeek({ data, view, glosses, onMore, onLookup, foot }) {
  const [peek, setPeek] = useState(null)
  const frame = useRef(null)
  // which card and which English each word on the chart is, lined up once per answer (tarkeebLayout.align)
  const onPage = useMemo(() => (data.tree?.tree ? layout(data.tree).written : []), [data.tree])
  // one card per typed word, in order: matched by place
  const cards = useMemo(() => align(onPage, data.words, 'word', { byPlace: true }), [onPage, data.words])
  const english = useMemo(() => align(onPage, glosses, 'arabic'), [onPage, glosses])
  const glossOf = (nth) => english[nth]?.english
  const open = (text, nth, el) => {
    const word = cards[nth]
    if (!word) return onLookup?.(text)
    const box = frame.current.getBoundingClientRect()
    const at = el.getBoundingClientRect()
    // kept inside the frame, so the panel never hangs off a phone's edge
    const half = Math.min(144, box.width / 2)
    const x = Math.min(Math.max(at.left + at.width / 2 - box.left, half), box.width - half)
    setPeek({ word, english: glossOf(nth), text, at: { x, y: at.bottom - box.top + 6 } })
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
