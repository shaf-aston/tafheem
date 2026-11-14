// The tapped dot's word, standing beside it on the picture: in the margin a figure leaves,
// against the drawing and never on it, with a thin line back to its dot. Where the drawing
// fills its box there is no margin and no label here; the card above says the word, as it
// always did. Where it stands is lib/colloquial/calloutPlace.js; this measures and draws.
import { useLayoutEffect, useRef } from 'react'

import ArabicText from '../../../ui/text/ArabicText'

/** `at` {x, y, w}: where it stands, in pixels from the picture's corner. `onHeight` tells the placer how tall it came out.
 * `tone` is its edge: the accent for a word explored, the danger colour for a wrong tap in Test. */
export default function Callout({ words, at, tone = 'var(--primary)', onHeight }) {
  const node = useRef(null)
  useLayoutEffect(() => {
    const el = node.current
    if (!el) return undefined
    const tell = () => onHeight(Math.ceil(el.getBoundingClientRect().height))
    tell()
    if (typeof ResizeObserver === 'undefined') return undefined
    const watch = new ResizeObserver(tell)
    watch.observe(el)
    return () => watch.disconnect()
  }, [onHeight, words])
  return (
    // Said again by the card, which is the live region: this is for the eye. It lets every tap through.
    <div ref={node} aria-hidden="true" data-callout
      className="absolute pointer-events-none rounded-[var(--radius-sm)] border bg-[var(--surface)] px-1.5 py-1 text-center shadow-sm"
      style={{ left: at.x, top: at.y, width: at.w, borderColor: tone }}>
      {words.map((w) => (
        <div key={w.id}>
          <ArabicText as="p" size="base" className="text-[var(--text)] leading-tight">{w.arabic}</ArabicText>
          <p className="type-micro text-[var(--text-dim)] leading-tight break-words">{w.english}</p>
        </div>
      ))}
    </div>
  )
}
