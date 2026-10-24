/**
 * Teach card: a new word and its meaning, before it is asked; `also` (optional) sets a second form beside it, smaller
 * (Basics: the word without ال, or the form an addition changes); `note` (optional) says the rule in a line.
 */
import ArabicText from '../../ui/ArabicText'
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

// The rule is an English line with a little Arabic in it (ـَتْ, لَمْ): each Arabic run is set in the Arabic face, on its own.
const ARABIC_RUN = /([\u0600-\u06FF](?:[\u0600-\u06FF ]*[\u0600-\u06FF])?)/
const ARABIC = /^[\u0600-\u06FF]/

const Note = ({ text }) => (
  <p className="grow-teach-note">
    {text.split(ARABIC_RUN).map((piece, at) => (ARABIC.test(piece) ? <ArabicText key={at} size="sm">{piece}</ArabicText> : piece))}
  </p>
)

export default function TeachCard({ card }) {
  return (
    <div className="grow-card grow-teach">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <ArabicText as="p" size="lg" className="grow-teach-ar">{card.ar}</ArabicText>
      <p className="grow-teach-en">{card.en}</p>
      {card.also && (
        <p className="grow-teach-also">
          <ArabicText size="base">{card.also.ar}</ArabicText>
          <span>{card.also.en}</span>
        </p>
      )}
      {card.note && <Note text={card.note} />}
    </div>
  )
}
