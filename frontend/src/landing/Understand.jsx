import { Fragment, useRef, useState } from 'react'

import { reducedMotion } from './motion.js'
import useScrollProgress, { settleProgress } from './useScrollProgress.js'

const LINE = 'Are you ready to understand?'

// Where each letter starts: x, y, depth and turn, each -0.5 to 0.5, scaled in the CSS.
// Seeded, so the letters scatter the same way on every visit.
let seed = 7
const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647 - 0.5
const WORDS = LINE.split(' ').map((word) => [...word].map((ch) => ({ ch, at: [rand(), rand(), rand(), rand()] })))

// The question's letters settle out of a scatter as the band scrolls up; three gold
// rings orbit behind and lean toward the pointer.
export default function Understand() {
  const ref = useRef(null)
  const [still] = useState(reducedMotion)
  const [lean, setLean] = useState(null)
  const settle = useScrollProgress(ref, settleProgress) // --a, read by the CSS

  function follow(e) {
    const r = e.currentTarget.getBoundingClientRect()
    setLean({ '--lx': (e.clientX - r.left) / r.width - 0.5, '--ly': (e.clientY - r.top) / r.height - 0.5 })
  }

  return (
    <section className="understand" ref={ref} style={{ '--a': still ? 1 : settle }}>
      <div className="understand-stage" onPointerMove={follow} onPointerLeave={() => setLean(null)}>
        <div className="understand-rings" aria-hidden="true" style={lean ?? undefined}><b /><b /><b /></div>
        <p className="understand-line">
          <span className="sr-only">{LINE}</span>
          {WORDS.map((letters, w) => (
            <Fragment key={w}>
              {w > 0 && ' '}
              <span aria-hidden="true" className={w === WORDS.length - 1 ? 'gold' : undefined}>
                {letters.map(({ ch, at: [dx, dy, dz, dr] }, i) => <span key={i} style={{ '--dx': dx, '--dy': dy, '--dz': dz, '--dr': dr }}>{ch}</span>)}
              </span>
            </Fragment>
          ))}
        </p>
      </div>
    </section>
  )
}
