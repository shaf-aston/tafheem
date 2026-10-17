/**
 * The "Show more (n left)" button under a paged list. Every infinite list drew
 * its own copy of this; it lives here once so the wording and the busy state
 * match from list to list.
 */
export default function LoadMore({ left, busy, onClick }) {
  return (
    <button
      type="button"
      disabled={busy}
      onClick={() => onClick()}
      className="press type-ui text-[var(--text-dim)] hover:text-[var(--text)] transition-colors"
    >
      {busy ? 'Loading…' : `Show more (${left} left)`}
    </button>
  )
}
