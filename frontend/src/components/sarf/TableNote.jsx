/**
 * Saying no is an answer too. A weak root or a noun has no gardaan, and this
 * panel gives the reason in full rather than looking like something failed.
 */
export default function TableNote({ accent, title = 'Why there is no table', children }) {
  return (
    <div style={{ '--c': accent }} className="card card-accent rise-in space-y-1">
      <div className="eyebrow">{title}</div>
      <p className="type-body leading-relaxed text-[var(--text-dim)]">{children}</p>
    </div>
  )
}
