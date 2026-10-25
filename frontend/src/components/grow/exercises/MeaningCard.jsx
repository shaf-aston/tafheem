/**
 * Which meaning is this word? The quiz's own question; marks right/wrong once checked.
 */
import ArabicText from '../../ui/ArabicText'
import OneOf from './OneOf'
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function MeaningCard({ card, value, setValue, result }) {
  const { question } = card
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask">{say(card.ask ?? 'What does this mean?')}</p>
      <ArabicText as="p" size="lg" className="grow-card-word">{question.prompt}</ArabicText>
      <OneOf options={question.options} answer={question.answerId} value={value} setValue={setValue} result={result} label={say('Meanings')} />
    </div>
  )
}
