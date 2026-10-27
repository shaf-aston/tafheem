/**
 * One question of a round, as a small square with its number inside: green for
 * right, red for wrong, a dashed outline for one not answered yet, orange
 * for the one on screen. Press it to put that question back on screen.
 *
 * The Quiz's strip and Tamreen's both draw this, and the Quiz draws it twice,
 * once for a question already answered and once for the one you are on. Drawn
 * here so the size, the radius and the fade stay one decision.
 */
const TONE = { right: 'var(--success)', wrong: 'var(--danger)', '': 'var(--border-hi)' }

export default function AnswerSquare({ status = '', number, current, label, onClick }) {
  const tone = current && !status ? 'var(--warn)' : TONE[status]
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={current}
      aria-label={label}
      style={{
        color: status ? tone : current ? 'var(--text)' : 'var(--text-faint)',
        borderColor: tone,
        background: status ? `color-mix(in srgb, ${tone} 16%, transparent)` : 'transparent',
        outline: current && status ? '2px solid var(--warn)' : undefined,
        outlineOffset: 2,
      }}
      className={`shrink-0 w-9 h-9 grid place-items-center rounded-[var(--radius-sm)] border type-ui font-bold
        tabular-nums leading-none transition-opacity hover:opacity-100
        ${current ? '' : 'opacity-80'} ${status ? '' : 'border-dashed'}`}
    >
      {number}
    </button>
  )
}
