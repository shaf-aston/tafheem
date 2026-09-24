/**
 * Ready-made inputs. Clicking one fills the box and runs it, a single click
 * takes a first-time reader all the way to a result.
 *
 * Accepts plain strings or { arabic, meaning } objects; `onPick` always
 * receives the Arabic string.
 */
import ArabicText from './ArabicText'

export default function ExampleChips({ label = 'Try one', examples, onPick, accent }) {
  return (
    <div className="flex flex-wrap gap-2 items-center" style={{ '--c': accent }}>
      <span className="text-[var(--text-faint)] text-xs shrink-0">{label}</span>
      {examples.map((ex, i) => {
        const arabic = typeof ex === 'string' ? ex : ex.arabic
        const meaning = typeof ex === 'object' ? ex.meaning : null
        return (
          <button
            key={arabic}
            type="button"
            onClick={() => onPick(arabic)}
            style={{ '--i': i }}
            className="rise-in flex flex-col items-end gap-0.5 px-3 py-1.5 rounded-[var(--radius-md)]
              bg-[var(--surface)] border border-[var(--border)] text-[var(--text-dim)]
              hover:border-[var(--c)] hover:text-[var(--text)] transition-colors"
          >
            <ArabicText className="leading-tight">{arabic}</ArabicText>
            {meaning && (
              <span className="text-[var(--text-faint)] type-tiny leading-tight" dir="ltr">{meaning}</span>
            )}
          </button>
        )
      })}
    </div>
  )
}
