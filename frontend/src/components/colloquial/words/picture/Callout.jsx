// A tapped place's word, standing in the picture's rail level with its place (lib/colloquial/labelRail.js),
// with its speaker: the word's one place on screen while it is shown, and its live region. The same on
// every board. Placed in shares of the picture, so it moves with it at any size; only its height is measured.
import { useLayoutEffect, useRef } from 'react'

import SpeakButton from '../../../ui/buttons/SpeakButton'
import ArabicText from '../../../ui/text/ArabicText'

<<<<<<< HEAD
const pct = (n) => `${n * 100}%`

/** `at` {x, y, w}: where it stands, in the board's units; `view`: the picture's view (with its rail).
 * `tone` is its edge: the accent for a word explored, the danger colour for a wrong tap in Test.
 * `hear` says the first word on each rise; `onHeight` tells the board how tall it came out, in pixels. */
export default function Callout({ words, at, view, tone = 'var(--primary)', hear = 0, compact = false, onHeight }) {
=======
/** `at` {x, y, w}: where it stands, in pixels from the picture's corner. `onHeight` tells the placer how tall it came out.
 * `tone` is its edge: the accent for a word explored, the danger colour for a wrong tap in Test. */
export default function Callout({ words, at, tone = 'var(--primary)', hear = 0, onHeight }) {
>>>>>>> origin/master
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
  const [vx, vy, vw, vh] = view
  return (
<<<<<<< HEAD
=======
    // Where it stands, the card above is not shown: this is the word's one place, its live region and its speaker.
>>>>>>> origin/master
    // Taps pass through it to the picture, except on the speaker.
    <div ref={node} aria-live="polite" data-callout
      className="absolute pointer-events-none rounded-[var(--radius-sm)] border bg-[var(--surface)] px-1.5 py-1 text-center shadow-sm"
      style={{ left: pct((at.x - vx) / vw), top: pct((at.y - vy) / vh), width: pct(at.w / vw), borderColor: tone }}>
      {words.map((w) => (
        <div key={w.id}>
          <ArabicText as="p" size={compact ? 'sm' : 'base'} className="text-[var(--text)] leading-tight">{w.arabic}</ArabicText>
          <p className="type-micro text-[var(--text-dim)] leading-tight break-words">{w.english}</p>
          {/* Only the first word is said on a tap (`hear`); the others wait for their button. */}
          <SpeakButton text={w.arabic} hear={w === words[0] ? hear : 0} className="pointer-events-auto mx-auto mt-0.5" />
        </div>
      ))}
    </div>
  )
}
