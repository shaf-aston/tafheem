import { useRef, useState } from 'react'

import { reducedMotion } from './motion.js'
import links from './links.json'
import useScrollProgress, { riseProgress } from './useScrollProgress.js'

// The wordmark and the button are one link into the app; pointing at it floods the wordmark gold.
export default function Finale() {
  const ref = useRef(null)
  const [still] = useState(reducedMotion)
  const rise = useScrollProgress(ref, riseProgress) // --e: how far the section has risen, read by the CSS

  return (
    <section className="finale" ref={ref} style={{ '--e': still ? 1 : rise }}>
      <div className="wrap">
        <a href={links.tool} className="finale-link">
          <span className="finale-mark" aria-hidden="true">Tafheem</span>
          <span className="cta">Open the tool</span>
        </a>
      </div>
    </section>
  )
}
