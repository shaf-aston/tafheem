/**
 * Where the reader is inside a section: Seerah › Hijrah › The cave of Thawr.
 *
 * Not the app's Trail (ui/Trail), which is the way back through what was read;
 * this is the level being read now, and each rung above is a press away. Drawn
 * in the Trail's quiet weights so the two read as one family.
 */
import { readingOrder } from '../lib/timelineLayout'

export default function TimelineWhere({ section, event, here, onHere, onPick }) {
  const at = readingOrder(event.steps).find((r) => r.step.id === here)
  const rungs = [
    { key: 'section', text: section.name, go: () => onPick(null) },
    { key: 'event', text: event.title, go: () => onHere(null) },
    ...(at ? [...at.above, at.step].map((s) => ({ key: s.id, text: s.title, go: () => onHere(s.id) })) : []),
  ]

  return (
    <nav aria-label="Where you are in this timeline" className="flex items-center gap-1.5 flex-wrap type-small text-[var(--text-faint)] min-w-0">
      {rungs.map((rung, i) => (
        <span key={rung.key} className="flex items-center gap-1.5 min-w-0">
          {i > 0 && <span aria-hidden="true" className="opacity-40">›</span>}
          {i === rungs.length - 1
            ? <span aria-current="location" className="text-[var(--text-dim)]">{rung.text}</span>
            : (
              <button
                type="button"
                onClick={rung.go}
                className="underline decoration-dotted underline-offset-4 hover:text-[var(--c)] transition-colors"
              >
                {rung.text}
              </button>
            )}
        </span>
      ))}
    </nav>
  )
}
