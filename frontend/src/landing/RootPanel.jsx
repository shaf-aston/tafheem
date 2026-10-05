import { useRef, useState } from 'react'

import { BOOKS, ROOT_LETTERS, ROOT_WORDS } from './storyData.js'

const HOT_MS = 700 // how long a tapped chip stays lit
const HIT_MS = 380 // how long a tapped letter stays lit

// Chip positions are pure CSS from these: the angle's cosine and sine, the
// slot in the phone grid, and the depth that scales the cursor drift.
const CHIP_VARS = ROOT_WORDS.map(([, , deg], i) => ({
  '--cos': Math.cos((deg * Math.PI) / 180).toFixed(3),
  '--sin': Math.sin((deg * Math.PI) / 180).toFixed(3),
  '--col': i % 3,
  '--row': Math.floor(i / 3),
}))

// The root's letters with the words it gives flying out around them as lp
// grows. A tap on a letter ripples, lights it and pulls the next word out.
export default function RootPanel({ lp }) {
  const stageRef = useRef(null)
  const nextHot = useRef(0)
  const [pinned, setPinned] = useState(0)
  const [hot, setHot] = useState(-1)
  const [hit, setHit] = useState(-1)
  const [rings, setRings] = useState([])
  const [drift, setDrift] = useState([0, 0])

  const shown = Math.floor(lp * 1.2 * (ROOT_WORDS.length + 1))
  const open = Math.max(shown, pinned)

  function move(e) {
    const r = stageRef.current.getBoundingClientRect()
    setDrift([((e.clientX - r.left) / r.width - 0.5) * 2, ((e.clientY - r.top) / r.height - 0.5) * 2])
  }

  function tap(e, i) {
    const r = stageRef.current.getBoundingClientRect()
    const lr = e.currentTarget.getBoundingClientRect()
    const x = e.clientX ? e.clientX - r.left : lr.left - r.left + lr.width / 2
    const y = e.clientY ? e.clientY - r.top : lr.top - r.top + lr.height / 2
    setHit(i)
    setTimeout(() => setHit(-1), HIT_MS)
    setRings((rs) => [...rs, { id: performance.now(), x, y }])
    if (open < ROOT_WORDS.length) setPinned(open + 1)
    else lightChip(nextHot.current++ % ROOT_WORDS.length)
  }

  function lightChip(i) {
    setHot(i)
    setTimeout(() => setHot(-1), HOT_MS)
  }

  return (
    <div className="story-rootstage" ref={stageRef} onPointerMove={move} onPointerLeave={() => setDrift([0, 0])}>
      <div className="story-roots" lang="ar" dir="rtl" style={{ '--px': drift[0], '--py': drift[1], '--lp': lp }} aria-label="The root kaf ta ba">
        {ROOT_LETTERS.map((l, i) => (
          <span
            key={l} className={`story-ltr${hit === i ? ' hit' : ''}`} style={{ '--d': i + 1 }}
            role="button" tabIndex={0} aria-label={l}
            onClick={(e) => tap(e, i)}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.currentTarget.click() } }}
          >{l}</span>
        ))}
      </div>
      <div className="story-bloom">
        {ROOT_WORDS.map(([ar, en], i) => (
          <button
            key={ar} type="button" style={CHIP_VARS[i]}
            className={`story-rchip${i < open ? ' on' : ''}${hot === i ? ' hot' : ''}`}
            onClick={() => lightChip(i)}
          >
            <span className="arabic" lang="ar">{ar}</span>
            <span className="story-gloss">{en}</span>
          </button>
        ))}
      </div>
      {rings.map((r) => (
        <span key={r.id} className="story-ring" style={{ left: r.x, top: r.y }} aria-hidden="true"
          onAnimationEnd={() => setRings((rs) => rs.filter((x) => x.id !== r.id))} />
      ))}
      <div className="story-books">
        {BOOKS.map(([name, what], i) => (
          <div key={name} className={`story-book${lp > 0.08 + i * 0.1 ? ' on' : ''}`}>
            <b>{name}</b>
            <span>{what}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
