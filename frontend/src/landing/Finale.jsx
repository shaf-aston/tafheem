import { useRef, useState } from 'react'

import { reducedMotion } from './motion.js'
import links from './links.json'
import useScrollProgress, { riseProgress } from './useScrollProgress.js'

export default function Finale() {
  const ref = useRef(null)
  const [flood, setFlood] = useState(false)
  const [still] = useState(reducedMotion)
  const rise = useScrollProgress(ref, riseProgress) // --e: how far the section has risen, read by the CSS

  return (
    <section className="finale" ref={ref} style={{ '--e': still ? 1 : rise }}>
      <div className="wrap">
        <div
          className={`finale-mark${flood ? ' flood' : ''}`} role="button" tabIndex={0} aria-label="Tafheem"
          onClick={() => setFlood((f) => !f)}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setFlood((f) => !f) } }}
        >Tafheem</div>
        <a href={links.tool} className="cta">Open the tool</a>
      </div>
    </section>
  )
}
