/** A new word, shown before it is asked: the Arabic, its meaning, and nothing to get wrong. */
import ArabicText from '../../ui/ArabicText'
import { sayIn } from '../../../lib/say'

const say = sayIn('en')

export default function TeachCard({ card }) {
  const { word } = card
  return (
    <div className="grow-card grow-teach">
      <span className="grow-card-tag">{say('New word')}</span>
      <ArabicText as="p" size="lg" className="grow-teach-ar">{word.ar}</ArabicText>
      <p className="grow-teach-en">{word.en}</p>
    </div>
  )
}
