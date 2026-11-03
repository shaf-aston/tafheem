/**
 * A number that rolls, like a meter: each digit is a column of 0 to 9 slid to
 * its value, so when the number changes only the digits that changed move
 * (.odometer in motion.css). XP, a streak, a score.
 *
 * The number itself is what a screen reader hears and what is copied; the
 * columns are drawn beside it and hidden from both. Keyed by the number's
 * length, so a digit gained or lost appears rather than every column rolling.
 */
const DIGITS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

export default function Odometer({ value, className = '' }) {
  const said = String(value)
  return (
    <span className={`odometer ${className}`}>
      <span className="sr-only">{said}</span>
      <span aria-hidden="true" key={said.length}>
        {[...said].map((ch, i) => (/\d/.test(ch) ? (
          <span key={i} className="odometer-digit">
            <span style={{ '--d': ch }}>{DIGITS.map((d) => <span key={d}>{d}</span>)}</span>
          </span>
        ) : <span key={i}>{ch}</span>))}
      </span>
    </span>
  )
}
