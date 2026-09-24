/**
 * One question of a round, as a small square with its number under it: a tick
 * for right, a cross for wrong, a dashed outline for one not answered yet.
 * Press it to put that question back on screen.
 *
 * The Quiz's strip and Tamreen's both draw this, and the Quiz draws it twice,
 * once for a question already answered and once for the one you are on. Drawn
 * here so the size, the radius and the fade stay one decision.
 */
const TONE = { right: 'var(--success)', wrong: 'var(--danger)', '': 'var(--border-hi)' }
const MARK = { right: '✓', wrong: '✕' }

export default function AnswerSquare({ status = '', number, current, label, accent, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={current}
      aria-label={label}
      className="flex flex-col items-center gap-0.5 group"
    >
      <span
        aria-hidden="true"
        style={{
          color: TONE[status],
          borderColor: current && accent ? accent : TONE[status],
          opacity: current ? 1 : 0.55,
        }}
        className={`w-5 h-5 grid place-items-center rounded-[var(--radius-sm)] border type-small
          leading-none transition-opacity group-hover:opacity-100 ${status ? '' : 'border-dashed'}`}
      >
        {MARK[status] ?? ''}
      </span>
      <span
        aria-hidden="true"
        className={`type-micro tabular-nums leading-none transition-colors
          ${current ? 'text-[var(--text)]' : 'text-[var(--text-faint)]'}`}
      >
        {number}
      </span>
    </button>
  )
}
