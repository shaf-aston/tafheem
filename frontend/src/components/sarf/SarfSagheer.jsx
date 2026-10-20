import ArabicText from '../ui/ArabicText'
import BlockTitle from './BlockTitle'
import SlotHead from './SlotHead'

/**
 * The sarf sagheer, the one line a book puts at the head of a baab, and the
 * part a reader actually memorises. It belongs above the grid, not under it.
 */
export default function SarfSagheer({ summary, accent }) {
  return (
    <div style={{ '--c': accent }} className="card card-accent rise-in space-y-3">
      <BlockTitle label="Sarf sagheer" term="صرف صغير" />
      {/* The book reads the باب out right to left, ماضي first, on the right; 
          so the slots are laid out that way too, same as the grid below. */}
      <div dir="rtl" className="grid gap-2 grid-cols-[repeat(auto-fit,minmax(8rem,1fr))]">
        {summary.map((slot, i) => (
          <div key={slot.label} style={{ '--i': i }} className="tile rise-in text-center">
            <SlotHead label={slot.label} term={slot.term} />
            <ArabicText className="block mt-1 text-[var(--text)]">{slot.arabic}</ArabicText>
          </div>
        ))}
      </div>
    </div>
  )
}
