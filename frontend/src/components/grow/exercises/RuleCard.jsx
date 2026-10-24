/** Teach card for a book world: what it means in plain English first, then the book's own sentence under it. */
import ArabicText from '../../ui/ArabicText'
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function RuleCard({ card }) {
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-rule-title">{card.title}</p>
      <p className="grow-rule-en">{card.en}</p>
      <figure className="grow-rule-book">
        <figcaption>{say('The book’s words')}</figcaption>
        <ArabicText as="p" className="grow-rule-ar">{card.ar}</ArabicText>
      </figure>
    </div>
  )
}
