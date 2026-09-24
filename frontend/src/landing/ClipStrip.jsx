import { useEffect, useRef, useState } from 'react'
import Reveal from './Reveal.jsx'
import { useInView } from '../lib/useInView'
import { CLIPS } from './assets/clips.js'

const LABELS = {
  nahw: 'Nahw', sarf: 'Sarf', quran: "Qur’an", daleel: 'Daleel',
  mem: 'Memorise', dict: 'Dictionary', quiz: 'Quiz', timelines: 'Timelines',
}
const ORDER = ['nahw', 'sarf', 'quran', 'daleel', 'mem', 'dict', 'quiz', 'timelines']
const items = ORDER.map((id) => CLIPS.find((c) => c.id === id))

function StripItem({ item }) {
  const [ref, inView] = useInView({ threshold: 0.6 })
  const videoRef = useRef(null)
  const [reduced] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches)

  // useInView latches true forever, so it also gates the one-time lazy load.
  const active = inView && !reduced

  useEffect(() => {
    if (!active) return
    videoRef.current?.play().catch(() => {})
  }, [active])

  return (
    <div className="strip-item" ref={ref}>
      <img src={item.poster} alt="" loading="lazy" />
      <video
        ref={videoRef}
        className={active ? 'lazy-clip show' : 'lazy-clip'}
        src={active ? item.src : undefined}
        poster={item.poster}
        muted
        loop
        playsInline
        preload="none"
      />
      <div className="cap">{LABELS[item.id]}</div>
    </div>
  )
}

// Horizontal scroll-snap strip of all eight tools, one per app section.
export default function ClipStrip() {
  return (
    <section className="strip-wrap" id="work">
      <div className="wrap">
        <Reveal as="h2" className="strip-heading">Eight tools, one scroll.</Reveal>
      </div>
      <div className="strip">
        {items.map((item) => <StripItem item={item} key={item.id} />)}
      </div>
    </section>
  )
}
