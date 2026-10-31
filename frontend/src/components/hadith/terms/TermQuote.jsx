/**
 * A term's words as its source prints them, folded behind "Quote: book, page".
 * The term card and the chain's guide to terms both show it; one place, so the
 * label and the Arabic read the same in both.
 */
import ArabicText from '../../ui/text/ArabicText'
import Disclosure from '../../ui/overlays/Disclosure'

export default function TermQuote({ quote, source, page }) {
  if (!quote) return null
  return (
    <Disclosure label={`Quote: ${[source, page].filter(Boolean).join(', ')}`}>
      <ArabicText as="p" size="sm" className="block m-0 leading-loose text-[var(--text-faint)]">{quote}</ArabicText>
    </Disclosure>
  )
}
