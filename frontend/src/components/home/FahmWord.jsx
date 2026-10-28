/**
 * Home's quiet word, فهم ("understanding"), beside the Resume card. At rest it
 * floats. Rest the pointer on it (or tap it on a phone) and understanding
 * arrives as weather: clouds, a quick shower the letters soak up, a sprout
 * from the هاء that opens into a flower. Every few hovers, a small party of
 * nuqat and harakat. Every timing is theme.json's fahm group; the moves are
 * styles/motion.css .fahm. Everything is drawn in one clipping svg, so
 * nothing leaves the word's box.
 */
import { useEffect, useId, useMemo, useRef, useState } from 'react'

import theme from '../../config/theme.json'
import { burst, ration } from '../../lib/motion/fahm'
import { motionOff } from '../../lib/motion/motion'

const KNOBS = theme.fahm
const WORD = 'فهم'

// The drawing's own space, and where Noto Naskh at 100px puts the ink in it.
const W = 320
const H = 200
const CX = 160
const BASELINE = 120
const INK = { top: 56, bottom: 147 }
const SPROUT = { x: 172, y: 88 } // the top of the middle letter, the هاء
const PARTY = { count: 28, x: CX, y: 104, spread: 30 }

// The story's beats, in order; each one keeps what came before.
const BEATS = ['cloudy', 'raining', 'growing', 'bloom']

const CLOUD = 'M8,24 H44 A8,8 0 0 0 44,8 A11,11 0 0 0 23,5 A8,8 0 0 0 10,12 A6,6 0 0 0 8,24 Z'
const Cloud = ({ x, y, s }) => <path className="fahm-cloud" d={CLOUD} transform={`translate(${x},${y}) scale(${s})`} />

// delay: when the leaf opens, as a share of motion.enter-ms after the stem starts.
const Leaf = ({ x, y, turn, delay, flip }) => (
  <g transform={`translate(${x},${y}) rotate(${turn}) scale(${flip ? -1 : 1},1)`}>
    <path className="fahm-leaf" d="M0,0 C5,-7 13,-6 16,-1 C10,4 4,4 0,0 Z" style={{ '--d': delay }} />
  </g>
)

/** A shower's drops, scattered once: where each starts, how far it falls, and its delay as a share of a drop's fall. */
const shower = () => Array.from({ length: 18 }, () => {
  const x = 112 + Math.random() * 104
  const y = 30 + Math.random() * 10
  return { x, y, fall: 60 + Math.random() * 35, delay: Math.random() * 0.9 }
})

// One mark of the party, centred on its own origin.
const MARKS = [
  <rect key="0" className="fahm-bit-0" x={-2.4} y={-2.4} width={4.8} height={4.8} transform="rotate(45)" />,
  <line key="1" className="fahm-bit-1" x1={-4} y1={1.6} x2={4} y2={-1.6} />,
  <circle key="2" className="fahm-bit-2" r={2.6} />,
  <rect key="3" className="fahm-bit-3" x={-1.6} y={-1.6} width={3.2} height={3.2} transform="rotate(45)" />,
]

export default function FahmWord({ className = '' }) {
  const [beat, setBeat] = useState(0)
  const [bits, setBits] = useState([])
  const [drops] = useState(shower)
  const party = useMemo(() => ration({ min: KNOBS['party-min'], max: KNOBS['party-max'] }), [])
  const timers = useRef([])
  const partyOver = useRef(0)
  const playing = useRef(false)
  const soak = useId()

  const clear = () => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }
  const later = (ms, fn) => timers.current.push(setTimeout(fn, ms))
  useEffect(() => () => {
    clear()
    clearTimeout(partyOver.current)
  }, [])

  const celebrate = () => {
    if (!party() || motionOff()) return
    setBits(burst(PARTY).map((bit, i) => ({ ...bit, id: `${Date.now()}-${i}` })))
    // Its own timer: the story may rest before the party has landed.
    clearTimeout(partyOver.current)
    partyOver.current = setTimeout(() => setBits([]), KNOBS['party-ms'] * 1.2)
  }

  // countAfter: how long the pointer has to stay before this counts as a hover (a tap counts at once).
  const play = (countAfter) => {
    clear()
    playing.current = true
    later(countAfter, celebrate)
    if (motionOff()) return setBeat(BEATS.length)
    setBeat(1)
    later(KNOBS['rain-at-ms'], () => setBeat(2))
    later(KNOBS['grow-at-ms'], () => setBeat(3))
    later(KNOBS['bloom-at-ms'], () => setBeat(4))
  }
  const rest = () => {
    clear()
    playing.current = false
    setBeat(0)
  }

  const onPointerEnter = (e) => e.pointerType !== 'touch' && play(KNOBS['settle-ms'])
  const onPointerLeave = (e) => e.pointerType !== 'touch' && rest()
  // A tap plays the story once; a tap while it plays changes nothing.
  const onPointerDown = (e) => {
    if (e.pointerType !== 'touch' || playing.current) return
    play(0)
    later(KNOBS['tap-hold-ms'], rest)
  }

  // The rain clears once the flower is out; the rest holds until the pointer leaves.
  const on = BEATS.filter((name, i) => beat > i && !(name === 'cloudy' && beat === BEATS.length))
  return (
    <div aria-hidden="true" className={`fahm ${on.map((n) => `is-${n}`).join(' ')} ${className}`}
      onPointerEnter={onPointerEnter} onPointerLeave={onPointerLeave} onPointerDown={onPointerDown}>
      <svg viewBox={`0 0 ${W} ${H}`}>
        <defs>
          <mask id={soak} maskUnits="userSpaceOnUse" x={0} y={0} width={W} height={H}>
            <rect className="fahm-level" x={0} y={INK.top} width={W} height={INK.bottom - INK.top} fill="white" />
          </mask>
        </defs>
        <ellipse className="fahm-shadow" cx={CX} cy={160} rx={52} ry={3.5} />
        <g className="fahm-float">
          <text className="fahm-ink fahm-soak" x={CX} y={BASELINE} textAnchor="middle" lang="ar" mask={`url(#${soak})`}>{WORD}</text>
          <text className="fahm-ink fahm-line" x={CX} y={BASELINE} textAnchor="middle" lang="ar">{WORD}</text>
        </g>
        <g className="fahm-sky">
          <Cloud x={104} y={8} s={1.1} />
          <Cloud x={160} y={2} s={0.95} />
          {drops.map((d, i) => (
            <line key={i} className="fahm-drop" x1={d.x} y1={d.y} x2={d.x - 2} y2={d.y + 7} style={{ '--d': d.delay, '--fall': `${d.fall}px` }} />
          ))}
        </g>
        <g transform={`translate(${SPROUT.x},${SPROUT.y})`}>
          <path className="fahm-stem" d="M0,0 C-5,-10 6,-20 1,-36" pathLength={1} />
          <Leaf x={0} y={-12} turn={-20} delay={0.5} />
          <Leaf x={1} y={-22} turn={10} delay={0.76} flip />
          <g transform="translate(1,-38)">
            <g className="fahm-flower">
              {[0, 72, 144, 216, 288].map((turn) => (
                <ellipse key={turn} className="fahm-petal" cx={0} cy={-5} rx={3.2} ry={5} transform={`rotate(${turn})`} />
              ))}
              <circle className="fahm-heart" r={2.4} />
            </g>
          </g>
        </g>
        {bits.length > 0 && <circle key={bits[0].id} className="fahm-ring" cx={CX} cy={102} r={10} />}
        {bits.map((b) => (
          <g key={b.id} className="fahm-bit"
            style={{ '--x': `${b.x}px`, '--y': `${b.y}px`, '--dx': `${b.dx}px`, '--dy': `${b.dy}px`, '--spin': `${b.spin}deg`, '--pace': b.pace }}>
            {MARKS[b.kind]}
          </g>
        ))}
      </svg>
    </div>
  )
}
