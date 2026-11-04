import ArabicText from '../ui/text/ArabicText'

/** One fact about the word: its root, its pattern or its verb class. */
export default function InfoCard({ label, value, gloss, arabic, accent, i }) {
  return (
    <div
      dir="ltr"
      style={{ '--i': i, '--c': accent }}
      className="card rise-in"
    >
      <div className="eyebrow mb-1">{label}</div>
      {/* The card itself reads left to right, so the Arabic stays inline and
          starts where the label starts, a block would push it to the far edge
          and leave the label and the gloss pointing the other way. */}
      {arabic
        ? <ArabicText className="text-[var(--text)]">{value}</ArabicText>
        : <div className="type-body text-[var(--text)]">{value}</div>}
      {gloss && <div className="type-small text-[var(--text-dim)] mt-1 leading-snug">{gloss}</div>}
    </div>
  )
}
