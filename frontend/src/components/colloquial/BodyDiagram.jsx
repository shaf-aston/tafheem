/**
 * A schematic body figure for the "body" word group: a tap on a hotspot shows
 * that word below it. WordGrid's own tile grid still draws every word on its
 * own tile beneath this -- the diagram is an extra map onto it, not a
 * replacement, so a word with no hotspot here is never missing from the page.
 */
import { useState } from 'react'

import ArabicText from '../ui/ArabicText'
import SpeakButton from '../ui/SpeakButton'
import { hotspotsFor } from '../../lib/colloquial/bodyDiagram'
import { FOCUS } from './parts/Face'

export default function BodyDiagram({ words }) {
  const [activeId, setActiveId] = useState(null)
  const spots = hotspotsFor(words)
  if (spots.length === 0) return null

  const active = spots.find((s) => s.word.id === activeId)

  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
      <svg viewBox="0 0 200 340" className="w-full max-w-[200px] mx-auto block">
        <g fill="none" stroke="var(--border)" strokeWidth="2">
          <circle cx="100" cy="50" r="36" />
          <path d="M70 84 Q100 100 130 84 L140 180 Q100 200 60 180 Z" />
          <line x1="60" y1="180" x2="50" y2="300" />
          <line x1="140" y1="180" x2="150" y2="300" />
        </g>
        {spots.map(({ word, x, y }) => (
          <circle
            key={word.id}
            cx={x}
            cy={y}
            r={activeId === word.id ? 10 : 7}
            role="button"
            tabIndex={0}
            aria-pressed={activeId === word.id}
            aria-label={`${word.english} (${word.arabic})`}
            className={`cursor-pointer transition-[r] ${FOCUS}`}
            fill={activeId === word.id ? 'var(--primary)' : 'color-mix(in srgb, var(--primary) 55%, var(--surface))'}
            onClick={() => setActiveId(word.id)}
            onKeyDown={(e) => {
              if (e.key !== 'Enter' && e.key !== ' ') return
              e.preventDefault()
              setActiveId(word.id)
            }}
          />
        ))}
      </svg>
      {active && (
        <div className="mt-3 flex items-center justify-center gap-2">
          <ArabicText as="p" size="lg" className="text-[var(--text)]">{active.word.arabic}</ArabicText>
          <span className="type-micro text-[var(--text-dim)]">{active.word.english}</span>
          <SpeakButton text={active.word.arabic} />
        </div>
      )}
    </div>
  )
}
