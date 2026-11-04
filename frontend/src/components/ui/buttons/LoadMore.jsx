/**
 * The "Show more (n left)" button under a paged list. Every infinite list drew
 * its own copy of this; it lives here once so the wording and the busy state
 * match from list to list. `left` is left out where the count is not known.
 */
export default function LoadMore({ left, busy, onClick }) {
  return (
    <button
      type="button"
      disabled={busy}
      onClick={() => onClick()}
      className="press tap type-ui text-[var(--text-dim)] hover:text-[var(--text)] transition-colors"
    >
      {busy ? 'Loading…' : left == null ? 'Show more' : `Show more (${left} left)`}
    </button>
  )
}
