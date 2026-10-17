import ArabicText from '../ui/ArabicText'

/** A block's name, English then its Arabic term, used by every block here. */
export default function BlockTitle({ label, term }) {
  return (
    <span className="flex items-baseline gap-2 type-label text-[var(--text)] font-medium">
      {label}
      <ArabicText size="sm" className="arabic-inline text-[var(--text-faint)]">{term}</ArabicText>
    </span>
  )
}
