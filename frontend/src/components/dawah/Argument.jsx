import { useState } from 'react'

import { GoButton } from '../ui/RootActions'
import TimelineRefs from '../TimelineRefs'

// The reasoning as a numbered path. Step by step reveals one point per press,
// the way the argument would be made out loud; All at once is for reading.
export default function Argument({ points, library, accent, mode, copy, onGo }) {
  const [shown, setShown] = useState(1)
  const visible = mode === 'all' ? points : points.slice(0, shown)
  return (
    <div className="space-y-3">
      <ol className="space-y-0">
        {visible.map((point, i) => (
          <li key={point.title} className="rise-in relative flex gap-3 pb-4" style={{ '--i': mode === 'all' ? i : 0 }}>
            {i < points.length - 1 && (
              <span aria-hidden="true" className="absolute start-[0.8rem] top-7 bottom-0 border-s border-[var(--border)]" />
            )}
            <span
              aria-hidden="true"
              className="relative shrink-0 w-[1.6rem] h-[1.6rem] grid place-items-center rounded-full type-tiny font-semibold text-[var(--bg)]"
              style={{ background: accent }}
            >
              {i + 1}
            </span>
            <div className="space-y-1.5 pt-0.5">
              <p className="text-[var(--text-dim)] leading-relaxed">
                <strong className="font-semibold text-[var(--text)]">{point.title}:</strong> {point.text}
              </p>
              {/* The evidence sits under the point it proves, small, so the claim reads first. */}
              <div className="flex flex-wrap items-center gap-1.5 type-small">
                <em className="text-[var(--text-faint)]">{copy.evidence}</em>
                <TimelineRefs refs={point.refs} library={library} accent={accent} onGo={onGo} className="contents" />
                {point.note && <em className="text-[var(--text-faint)]">{point.note}</em>}
              </div>
            </div>
          </li>
        ))}
      </ol>
      {mode === 'steps' && shown < points.length && (
        <div className="flex items-center gap-3 ps-10">
          <GoButton onClick={() => setShown(shown + 1)}>{copy['next-point']}</GoButton>
          <span className="type-small text-[var(--text-faint)]">{copy['point-count'].replace('{shown}', shown).replace('{total}', points.length)}</span>
        </div>
      )}
    </div>
  )
}
