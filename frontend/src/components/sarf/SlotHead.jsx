import ArabicText from '../ui/text/ArabicText'

/** A slot's or a column's name: the same two lines in the table and above it. */
export default function SlotHead({ label, term }) {
  return (
    <>
      <div dir="ltr" className="eyebrow">{label}</div>
      {term && <ArabicText size="sm" className="block text-[var(--text-faint)]">{term}</ArabicText>}
    </>
  )
}
