import { useEffect, useRef, useState } from 'react'

import links from './links.json'

const LINES = ['Arabic, unlocked.', 'Grammar you can see.', 'Recitation you can trust.']
const RISE_SHARE = 0.85 // share of the section's height that has to scroll past before it is fully risen

// --e (0 to 1, eased) is how far the section has risen into view. Written
// straight to the element, not state, so a scroll frame restyles only this.
function useRise(ref) {
  useEffect(() => {
    const node = ref.current
    const still = matchMedia('(prefers-reduced-motion: reduce)').matches
    let raf = 0
    function frame() {
      raf = 0
      const r = node.getBoundingClientRect()
      const p = still ? 1 : Math.min(1, Math.max(0, (innerHeight - r.top) / (Math.min(r.height, innerHeight) * RISE_SHARE)))
      node.style.setProperty('--e', (1 - (1 - p) ** 3).toFixed(3))
    }
    function onScroll() { if (!raf) raf = requestAnimationFrame(frame) }
    frame()
    addEventListener('scroll', onScroll, { passive: true })
    addEventListener('resize', onScroll)
    return () => {
      removeEventListener('scroll', onScroll)
      removeEventListener('resize', onScroll)
      cancelAnimationFrame(raf)
    }
  }, [ref])
}

export default function Finale() {
  const ref = useRef(null)
  const [flood, setFlood] = useState(false)
  useRise(ref)

  return (
    <section className="finale" ref={ref}>
      <div className="wrap">
        <p className="finale-lines">
          {LINES.map((l, i) => <span key={l}><span style={{ '--i': i }}>{l}</span></span>)}
        </p>
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
