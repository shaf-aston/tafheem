import { useLayoutEffect, useRef, useState } from 'react'

import { isUnnamed, caseLabel, caseFrom } from '../../../lib/nahw/grammarTerms'
import { arc } from '../../../lib/nahw/govArc'
import { roleVar } from '../../../lib/nahw/roleColors'
import ArabicText from '../../ui/text/ArabicText'

// "X governs Y" or "Y follows X", the typed words themselves.
export function GovernsWhy({ words, i }) {
  const w = words[i]
  const from = <ArabicText size="sm" className="text-[var(--text)]">{words[caseFrom(w)].word}</ArabicText>
  const to = <ArabicText size="sm" className="text-[var(--text)]">{w.word}</ArabicText>
  return w.governor != null
    ?<>{from} governs {to}: it gives it its case.</>
    : <>{to} follows {from} and copies its case.</>
}

// Governs view: one unbroken line (arcs cannot cross a wrap) with an arc above it
// from each governor down into the word it governs; a follower's arc is dashed.
const ARC_CAP = 56 // px the tallest arc climbs above the words
export default function WordGrid({ words, onClick, governs, picked, corner }) {
  const lineRef = useRef(null)
  const [arcs, setArcs] = useState([])
  useLayoutEffect(() => {
    if (!governs) return undefined
    const line = lineRef.current
    function measure() {
      // Measured against the svg the arcs are drawn in, so no offsetParent can skew them.
      const box = line.querySelector('svg').getBoundingClientRect()
      const cards = [...line.querySelectorAll('.word')].map((c) => c.getBoundingClientRect())
      const at = (i) => [cards[i].left - box.left + cards[i].width / 2, cards[i].top - box.top]
      setArcs(words.flatMap((w, i) => (caseFrom(w) === undefined ? [] : [{
        i, dashed: w.governor == null, ...arc(at(caseFrom(w)), at(i), ARC_CAP),
      }])))
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(line)
    // The cards rise in; measure again once they have landed.
    line.addEventListener('animationend', measure)
    document.fonts?.ready.then(measure)
    return () => { ro.disconnect(); line.removeEventListener('animationend', measure) }
  }, [governs, words])

  // `corner` sits in the card's top-right, outside the scroller so it stays put.
  return (
    <div className="relative">
    {corner && <div className="absolute top-2 right-2 z-[var(--layer-raised)] opacity-70 hover:opacity-100">{corner}</div>}
    <div
      dir="rtl"
      className={`peer-dim p-5 rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
        ${corner ? 'pt-12' : ''} ${governs ? 'overflow-x-auto' : ''}`}
    >
      <div
        ref={lineRef}
        style={governs ? { paddingTop: ARC_CAP + 8 } : undefined}
        className={`relative flex justify-center gap-3 ${governs ? 'flex-nowrap w-max min-w-full' : 'flex-wrap'}`}
      >
      {governs && (
        <svg className="absolute inset-0 w-full h-full overflow-visible pointer-events-none" aria-hidden="true">
          {arcs.map((a) => (
            <g key={a.i} stroke={roleVar(words[a.i].role_key)} fill="none" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"
              className="transition-opacity" style={{ opacity: picked < 0 || picked === a.i ? 1 : 0.25 }}>
              <path d={a.d} strokeDasharray={a.dashed ? '4 5' : undefined} />
              <path d={a.head} />
            </g>
          ))}
        </svg>
      )}
      {words.map((word, i) => {
        const key = word.role_key
        return (
          <button
            key={`${word.word}-${i}`}
            type="button"
            onClick={() => onClick(word)}
            aria-label={`${word.word}, ${isUnnamed(word) ? 'not named, see why' : (word.name ?? word.role) || 'details'}`}
            style={{ '--i': i, '--c': roleVar(key) }}
            className="word rise-in role glow
              flex flex-col items-center gap-1.5 px-4 py-3 rounded-[var(--radius-md)]
              bg-[var(--surface-hi)] border"
          >
            <ArabicText className="text-glow leading-tight">{word.word}</ArabicText>
            {/* The term alone. What it means is in the glossary at the foot
                of the page, once, not under every tag. */}
            {word.role && (
              <span className="type-tiny px-2 py-0.5 rounded-full role-tag">
                {word.name ?? word.role}
              </span>
            )}
            {word.case && (
              <ArabicText size="tiny" className="text-[var(--text-faint)]">{caseLabel(word.case)}</ArabicText>
            )}
          </button>
        )
      })}
      </div>
    </div>
    </div>
  )
}
