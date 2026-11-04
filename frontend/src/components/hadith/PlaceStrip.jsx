/**
 * The places of the Hadith tab beside its books (Starred, Rijal, Scholars, Terms) as one line of chips under the
 * search box, all in view at once, slid sideways where a phone is too narrow. The open place is the filled chip;
 * pressing it again goes back to the books. Each item is { label, hint, count?, on, pick }.
 */
import Chip from '../ui/inputs/Chip'
import ChipRow from '../ui/inputs/ChipRow'

export default function PlaceStrip({ items, accent }) {
  return (
    <ChipRow scroll role="group" aria-label="Places in Hadith">
      {items.map(({ label, hint, count, on, pick }) => (
        <Chip key={label} tinted selected={on} accent={accent} title={hint} onClick={pick}>
          {label}
          {count > 0 && <span className="ms-1.5 tabular-nums">{count}</span>}
        </Chip>
      ))}
    </ChipRow>
  )
}
