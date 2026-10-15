/** Teach card: a new word and its meaning, before it is asked. */
import ArabicText from '../../ui/ArabicText'
import { sayIn } from '../../../lib/say'

const say = sayIn('en')

export default function TeachCard({ card }) {
  return (
    <div className="grow-card grow-teach">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <ArabicText as="p" size="lg" className="grow-teach-ar">{card.ar}</ArabicText>
      <p className="grow-teach-en">{card.en}</p>
    </div>
  )
}
