/**
 * A word picked out of the text around it: the reason a card is showing it.
 * Colour and an underline, so the word is found without seeing colour.
 */
export default function Mark({ accent, children }) {
  return (
    <mark className="bg-transparent underline underline-offset-8 decoration-2" style={{ color: accent }}>
      {children}
    </mark>
  )
}
