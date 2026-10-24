/**
 * Small dotted text that opens a sheet or turns one to another page: the one
 * look for "there is more to read here", set apart from a Chip, which filters
 * or changes what the page shows. `accent` colours it on hover.
 */
export default function SheetLink({ onClick, accent, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="press type-small text-[var(--text-dim)] hover:text-[var(--c)] underline underline-offset-4 decoration-dotted"
      style={{ '--c': accent }}
    >
      {children}
    </button>
  )
}
