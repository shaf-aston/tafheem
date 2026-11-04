import { useLayoutEffect, useRef, useState } from 'react'

import { arc } from '../lib/nahw/govArc'
import { roleVar } from '../lib/nahw/roleColors'
import { DEMO_WORDS, GOVERNS } from './storyData.js'

const tone = (w) => (w.tone !== undefined ? { '--tone': roleVar(w.tone) } : undefined)

// The whole sentence on one line, full-bleed, under a camera that slides along it:
// it rests on each word as it is named, then on each governed pair as its arrow is
// drawn. `phase` (storyPhase.js) says where; arrows sit above the words, and a strip
// of ticks (one per word) under the line. `notes` is what shows under it, per phase.
export default function SentencePanel({ phase, notes }) {
  const panRef = useRef(null)
  const lineRef = useRef(null)
  const [m, setM] = useState({ arcs: [], bounds: [], w: 0 })

  // Arrows start and end at real word positions, measured in the line's own
  // coordinates so the slide never disturbs them.
  useLayoutEffect(() => {
    const pan = panRef.current
    const line = lineRef.current
    function measure() {
      const words = [...line.querySelectorAll('.story-word')]
      const at = (i) => [words[i].offsetLeft + words[i].offsetWidth / 2, words[i].offsetTop]
      setM({
        arcs: GOVERNS.map((g) => arc(at(g.from), at(g.to))),
        bounds: words.map((w) => [w.offsetLeft, w.offsetLeft + w.offsetWidth]),
        w: pan.clientWidth,
      })
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(pan)
    ro.observe(line)
    document.fonts?.ready.then(measure)
    return () => ro.disconnect()
  }, [])

  const [a, b] = phase.focus
  const span = m.bounds.length ? [m.bounds[a], m.bounds[b]] : null
  const mid = span ? (Math.min(span[0][0], span[1][0]) + Math.max(span[0][1], span[1][1])) / 2 : 0
  const shift = span ? m.w / 2 - mid : 0
  const inFocus = (i) => i === a || i === b
  const naming = phase.phase === 'name'

  return (
    <>
      <div className="story-pan" ref={panRef}>
        <div className="story-line" ref={lineRef} lang="ar" dir="rtl" style={{ transform: `translateX(${shift}px)` }}>
          {DEMO_WORDS.map((w, i) => (
            <span className={`story-word${i < phase.named ? ' on' : ''}${inFocus(i) ? ' cur' : ''}`} key={w.word} style={tone(w)}>
              <span className="arabic">{w.word}</span>
              <span className="story-role arabic">{w.role}</span>
            </span>
          ))}
          <svg className="story-arcs" aria-hidden="true">
            {m.arcs.map((arrow, k) => (
              <g key={k} stroke={roleVar(DEMO_WORDS[GOVERNS[k].to].tone)}>
                <path d={arrow.d} pathLength="1" style={{ '--d': phase.drawn[k] }} />
                <path className="story-head" d={arrow.head} style={{ opacity: phase.drawn[k] > 0.95 ? 1 : 0 }} />
              </g>
            ))}
          </svg>
        </div>
      </div>
      <div className="story-ticks" aria-hidden="true">
        {DEMO_WORDS.map((w, i) => <i key={w.word} className={`${i < phase.named ? 'on' : ''} ${inFocus(i) ? 'act' : ''}`.trim()} style={tone(w)} />)}
      </div>
      <p className="story-pair">
        {naming ? `Word ${Math.max(1, phase.named)} of ${DEMO_WORDS.length}` : `Pair ${phase.pair + 1} of ${GOVERNS.length}`}
      </p>
      {/* Chips for the naming, a reason for each pair: all in one cell, the others faded
          out, so the panel is as tall as the tallest and nothing below it jumps. */}
      <div className="story-notes">
        {notes}
        {GOVERNS.map((g, k) => (
          <p key={k} className={`story-why${k === phase.pair && phase.why ? ' on' : ''}`} aria-hidden={k !== phase.pair}>
            <b lang="ar">{g.why[0]}</b> {g.why[1]}<b lang="ar">{g.why[2]}</b>{g.why[3]}
          </p>
        ))}
      </div>
    </>
  )
}
