// An ayah's (or a verse's) number, drawn one way in every tab: a small round outlined badge.
export default function AyahNumber({ children, className = '', ...rest }) {
  return (
    <span
      className={`shrink-0 type-small font-mono rounded-full px-2 py-0.5 border border-[var(--border)] text-[var(--text-faint)] ${className}`.trim()}
      {...rest}
    >
      {children}
    </span>
  )
}
