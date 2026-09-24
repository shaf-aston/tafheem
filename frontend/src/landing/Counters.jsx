import { useEffect, useRef, useState } from 'react'
import Reveal from './Reveal.jsx'
import { useInView } from '../lib/useInView'

const STATS = [
  { target: 34, label: 'classical books indexed', suffix: '' },
  { target: 1.2, label: 'word-error rate across 9,926 words, 7 reciters', suffix: '%', decimals: 1 },
  { target: 1950, label: 'real recitations scored word by word', suffix: '' },
  { target: 4641, label: "roots with Ibn Faris's origin sense", suffix: '' },
]

function Stat({ s }) {
  const [ref, inView] = useInView({ threshold: 0.5 })
  const [value, setValue] = useState(0)
  const startedRef = useRef(false)

  useEffect(() => {
    if (!inView || startedRef.current) return
    startedRef.current = true
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduced) { requestAnimationFrame(() => setValue(s.target)); return }
    const dur = 1400
    let start = null
    function step(ts) {
      if (!start) start = ts
      const p = Math.min((ts - start) / dur, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setValue(s.target * eased)
      if (p < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [inView, s.target])

  const decimals = s.decimals || 0
  const shown = decimals ? value.toFixed(decimals) : Math.round(value)

  return (
    <div className="stat reveal in" ref={ref}>
      <b>{shown}{s.suffix}</b>
      <span>{s.label}</span>
    </div>
  )
}

// Count-up statistics on the parchment band, each animating once it scrolls
// into view.
export default function Counters() {
  return (
    <section className="shift">
      <div className="wrap">
        <Reveal as="div" className="shift-head">
          <p>Every number below is measured against real corpora, not claimed.</p>
        </Reveal>
        <div className="stats">
          {STATS.map((s) => <Stat s={s} key={s.label} />)}
        </div>
      </div>
    </section>
  )
}
