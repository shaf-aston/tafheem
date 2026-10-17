/** Teach card for a book world: the book's sentence, then what it means in plain English. */
import ArabicText from '../../ui/ArabicText'
import { sayIn } from '../../../lib/say'

const say = sayIn('en')

export default function RuleCard({ card }) {
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-rule-title">{card.title}</p>
      <ArabicText as="p" className="grow-rule-ar">{card.ar}</ArabicText>
      <p className="grow-rule-en">{card.en}</p>
    </div>
  )
}
