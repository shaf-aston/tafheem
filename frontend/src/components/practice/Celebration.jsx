/**
 * The end-of-lesson medal: a burst of rays, a seed that sprouts in the gold
 * disc, and confetti thrown up and falling away (styles/growWorlds.css).
 *
 * Its own file so anything that celebrates can wear the same one, and the Kit
 * can show it, rather than a second medal drifting from this one. Decoration
 * only: the words beside it ("Lesson done", the numbers) say what happened.
 * Wear it inside an element that sets --w, the accent of the lesson.
 */

/** A burst round the medal: pieces in the theme's colours, spaced evenly. */
const BURST = Array.from({ length: 12 }, (_, i) => ({ angle: i * 30, tone: ['var(--w)', 'var(--grow-gold)', 'var(--success)'][i % 3] }))

/** Confetti thrown up from the medal: where each piece lands sideways (px), how far it turns, its colour. Fixed, so a replay is the same throw. */
export const CONFETTI = Array.from({ length: 24 }, (_, i) => ({
  x: (((i * 37) % 100) - 50) * 3.2,
  turn: ((i * 73) % 300) + 180,
  tone: ['var(--w)', 'var(--grow-gold)', 'var(--success)', 'var(--palette-rose)'][i % 4],
}))

/** The seed in the medal: it sits, then a stem rises and two leaves open (.grow-sprout). */
const Sprout = () => (
  <svg className="grow-sprout" viewBox="0 0 40 40" width="56" height="56">
    <ellipse className="grow-sprout-seed" cx="20" cy="33" rx="6" ry="4" />
    <path className="grow-sprout-stem" d="M20 31 C20 25 20 20 20 14" pathLength="1" />
    <path className="grow-sprout-leaf grow-sprout-left" d="M20 18 C14 18 10 14 9 9 C15 9 19 12 20 18Z" />
    <path className="grow-sprout-leaf grow-sprout-right" d="M20 15 C26 15 30 11 31 6 C25 6 21 9 20 15Z" />
  </svg>
)

export default function Medal() {
  return (
    <div className="grow-medal" aria-hidden="true">
      {BURST.map(({ angle, tone }) => <i key={angle} style={{ '--a': `${angle}deg`, '--tone': tone }} />)}
      <span className="pop"><Sprout /></span>
      {/* A div, not a span: .grow-medal span is the gold disc. */}
      <div className="grow-confetti">
        {CONFETTI.map(({ x, turn, tone }, i) => <i key={i} style={{ '--x': `${x}px`, '--turn': `${turn}deg`, '--tone': tone, '--i': i }} />)}
      </div>
    </div>
  )
}
