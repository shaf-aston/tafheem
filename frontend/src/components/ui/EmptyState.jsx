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
 */
export default function EmptyState({ children }) {
  return <p className="text-sm text-[var(--text-dim)] text-center py-8">{children}</p>
}
