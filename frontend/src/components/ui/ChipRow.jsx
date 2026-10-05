/**
 * One line of the strip between a search box and what it shows: a faint label,
 * then chips. Recent, Chapters, the collection row and the reading options all
 * use it, so every line there reads the same way. Dictionary's root choice is
 * the same line, so it uses it too.
 */
export default function ChipRow({ label, children, className = '', ...rest }) {
  return (
    <div className={`flex flex-wrap gap-1.5 items-center ${className}`} {...rest}>
      {label && <span className="text-[var(--text-faint)] type-small shrink-0">{label}</span>}
      {children}
    </div>
  )
}
