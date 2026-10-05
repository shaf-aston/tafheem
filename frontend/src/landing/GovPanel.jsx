import { useLayoutEffect, useRef, useState } from 'react'

import { arc } from '../lib/govArc'
import { roleVar } from '../lib/roleColors'
import { DEMO_WORDS, GOVERNS } from './storyData.js'

const clamp = (v) => Math.max(0, Math.min(1, v))

// One-line sentence that slides so the active pair sits in the middle, arrows
// above the words, and a strip of ticks (one per word) under it.
export default function GovPanel({ lp, govIdx }) {
  const panRef = useRef(null)
  const lineRef = useRef(null)
  const [m, setM] = useState({ arcs: [], mids: [], w: 0 })

  // Arrows start and end at real word positions, measured in the line's own
  // coordinates so the slide never disturbs them.
  useLayoutEffect(() => {
    const pan = panRef.current
    const line = lineRef.current
    function measure() {
      const words = [...line.querySelectorAll('.story-word')]
      const at = (i) => [words[i].offsetLeft + words[i].offsetWidth / 2, words[i].offsetTop]
      const mids = GOVERNS.map((g) => {
        const [a, b] = [words[g.from], words[g.to]]
        return (Math.min(a.offsetLeft, b.offsetLeft) + Math.max(a.offsetLeft + a.offsetWidth, b.offsetLeft + b.offsetWidth)) / 2
      })
      setM({ arcs: GOVERNS.map((g) => arc(at(g.from), at(g.to))), mids, w: pan.clientWidth })
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(pan)
    ro.observe(line)
    document.fonts?.ready.then(measure)
    return () => ro.disconnect()
  }, [])

  const pair = GOVERNS[govIdx]
  const shift = m.mids.length ? m.w / 2 - m.mids[govIdx] : 0
  const tone = (w) => (w.tone !== undefined ? { '--tone': roleVar(w.tone) } : undefined)

  return (
    <>
      <div className="story-pan" ref={panRef}>
        <div className="story-line" ref={lineRef} lang="ar" dir="rtl" style={{ transform: `translateX(${shift}px)` }}>
          {DEMO_WORDS.map((w, i) => (
            <span className={`story-word on${pair.from === i || pair.to === i ? ' cur' : ''}`} key={w.word} style={tone(w)}>
              <span className="arabic">{w.word}</span>
              <span className="story-role arabic">{w.role}</span>
            </span>
          ))}
          <svg className="story-arcs" aria-hidden="true">
            {m.arcs.map((a, k) => {
              const d = clamp(k === 0 ? lp * 3 : (lp - 0.35) * 3)
              const stroke = roleVar(DEMO_WORDS[GOVERNS[k].to].tone)
              return (
                <g key={k} stroke={stroke}>
                  <path d={a.d} pathLength="1" style={{ '--d': d }} />
                  <path className="story-head" d={a.head} style={{ opacity: d > 0.95 ? 1 : 0 }} />
                </g>
              )
            })}
          </svg>
        </div>
      </div>
      <div className="story-ticks" aria-hidden="true">
        {DEMO_WORDS.map((w, i) => <i key={w.word} className={pair.from === i || pair.to === i ? 'act' : ''} style={tone(w)} />)}
      </div>
      <p className="story-pair">Pair {govIdx + 1} of {GOVERNS.length}</p>
      {GOVERNS.map((g, k) => k === govIdx && (
        <p key={k} className={`story-why${lp > 0.25 ? ' on' : ''}`}>
          <b lang="ar">{g.why[0]}</b> {g.why[1]}<b lang="ar">{g.why[2]}</b>{g.why[3]}
        </p>
      ))}
    </>
  )
}
