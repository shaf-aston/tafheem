/**
 * Which meaning is this word? The quiz's own question; marks right/wrong once checked.
 */
import ArabicText from '../../ui/ArabicText'
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function MeaningCard({ card, value, setValue, result }) {
  const { question } = card
  const markOf = (option) => {
    if (!result) return option.id === value ? 'picked' : undefined
    if (option.id === question.answerId) return 'right'
    return option.id === value ? 'wrong' : undefined
  }
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask">{say(card.ask ?? 'What does this mean?')}</p>
      <ArabicText as="p" size="lg" className="grow-card-word">{question.prompt}</ArabicText>
      <div className="grow-options" role="radiogroup" aria-label={say('Meanings')}>
        {question.options.map((option) => (
          <button
            key={option.id}
            type="button"
            role="radio"
            aria-checked={option.id === value}
            className="grow-option"
            data-mark={markOf(option)}
            disabled={Boolean(result)}
            onClick={() => setValue(option.id)}
          >
            {option.text}
          </button>
        ))}
      </div>
    </div>
  )
}
