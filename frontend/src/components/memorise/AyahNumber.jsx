import { hitArea } from './hitArea'

// An ayah's (or a verse's) number, drawn one way in every tab: a small round outlined badge.
// Given `onClick` (reciting, once the ayah has been reached) it is a button that opens the ayah's card.
export default function AyahNumber({ children, className = '', onClick, ...rest }) {
  const look = `shrink-0 type-small font-mono rounded-full px-2 py-0.5 border border-[var(--border)] text-[var(--text-faint)] ${className}`.trim()
  if (!onClick) return <span className={look} {...rest}>{children}</span>
  return (
    <button
      type="button"
      onClick={onClick}
      className={`${look} ${hitArea} bg-transparent cursor-pointer hover:bg-[var(--surface-hi)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--c)]/40`}
      {...rest}
    >
      {children}
    </button>
  )
}
