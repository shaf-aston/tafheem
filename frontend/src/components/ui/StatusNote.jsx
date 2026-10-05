/**
 * One quiet line saying what happened to the request: a word swapped, a
 * search narrowed, a link that named nothing. Read out when it changes.
 * Not for an empty result (EmptyState) or a failure (ErrorAlert).
 */
export default function StatusNote({ children }) {
  return <p role="status" className="type-small text-[var(--text-dim)]">{children}</p>
}
