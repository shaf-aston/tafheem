/**
 * Which meaning is this word? The quiz's own question; marks right/wrong once checked. A Qur'anic word shows its ayah.
 */
import ArabicText from '../../ui/text/ArabicText'
import AyahLine from './AyahLine'
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
      {question.ayah && <AyahLine ayah={question.ayah} />}
      <OneOf options={question.options} answer={question.answerId} value={value} setValue={setValue} result={result} label={say('Meanings')} />
    </div>
  )
}
