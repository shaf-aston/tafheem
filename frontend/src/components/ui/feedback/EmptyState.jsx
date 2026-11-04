/**
 * "Nothing here", the same line, the same way, in every panel.
 *
 * Four panels each wrote their own, and they had drifted into three looks: two
 * paddings and two text colours for one idea. Someone moving between tabs should
 * not have to work out whether a line that looks different means a different
 * kind of nothing.
 *
 * This is for an empty result, never for a failure. A search that found nothing
 * is an answer; a search that could not run is an ErrorAlert with something to
 * retry, and the two must not look alike.
 *
 * Above the line, a scatter of dots drifts together into a question mark, and
 * then the line arrives (.dots-gather in motion.css): a moment of character for
 * an answer that is otherwise just a shrug. Drawn only; the words say it.
 */

// Where each dot lands, on a 24 × 32 grid, and where it starts from.
const DOTS = [
  [6, 9, -9, 6], [8, 5, -6, -8], [12, 3, 2, -10], [16, 5, 9, -6], [18, 9, 10, 4],
  [16, 13, 8, 10], [12, 16, -10, 8], [12, 20, 6, 9], [12, 27, -4, 4],
]

export default function EmptyState({ children }) {
  return (
    <div className="dots-gather text-center py-8 space-y-2">
      <svg viewBox="0 0 24 32" width="24" height="32" aria-hidden="true" className="mx-auto text-[var(--text-faint)]">
        {DOTS.map(([x, y, dx, dy], i) => (
          <circle key={i} cx={x} cy={y} r="1.6" fill="currentColor" style={{ '--dx': `${dx}px`, '--dy': `${dy}px`, '--i': i }} />
        ))}
      </svg>
      <p className="type-ui text-[var(--text-dim)]">{children}</p>
    </div>
  )
}
