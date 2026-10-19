/** One tab on Home: its name in its own colour, what you do there, and your progress in it. */
import ArabicText from '../ui/ArabicText'

export default function ModuleCard({ tab, accent, progress, onOpen, onHover }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(tab.id)}
      onMouseEnter={() => onHover?.(tab.id)}
      onFocus={() => onHover?.(tab.id)}
      className="tap press text-start rounded-[var(--radius-sm)] border border-[var(--border)] p-3 space-y-1
        hover:bg-[var(--surface)] transition-colors"
      style={{ '--c': accent }}
    >
      <span className="flex items-baseline justify-between gap-2">
        <span className="font-bold" style={{ color: accent }}>{tab.label}</span>
        <ArabicText size="sm" className="text-[var(--text-faint)]">{tab.arabic}</ArabicText>
      </span>
      <span className="block type-small text-[var(--text-dim)]">{tab.blurb}</span>
      {progress && (
        <span className="block type-small tabular-nums text-[var(--text-faint)]">
          {progress.learnt} learnt · {progress.attempts} {progress.attempts === 1 ? 'answer' : 'answers'}
        </span>
      )}
    </button>
  )
}
