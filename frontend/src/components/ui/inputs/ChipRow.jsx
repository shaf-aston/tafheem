/**
 * One line of the strip between a search box and what it shows: a faint label,
 * then chips. Recent, Chapters, the collection row and the reading options all
 * use it, so every line there reads the same way. Dictionary's root choice is
 * the same line, so it uses it too.
 *
 * `scroll` keeps a long row on one line on a phone, slid sideways, instead of
 * wrapping into a block that pushes what it filters off the screen.
 */
export default function ChipRow({ label, scroll = false, children, className = '', ...rest }) {
  const wrap = scroll ? 'overflow-x-auto sm:flex-wrap -mx-1 px-1 pb-1 [&>*]:shrink-0' : 'flex-wrap'
  return (
    <div className={`flex ${wrap} gap-1.5 items-center ${className}`} {...rest}>
      {label && <span className="text-[var(--text-faint)] type-small shrink-0">{label}</span>}
      {children}
    </div>
  )
}
