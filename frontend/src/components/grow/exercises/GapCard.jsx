/** Complete the hadith: its key line with one word blanked, four words to choose from. */
import ArabicText from '../../ui/ArabicText'
import { sayIn } from '../../../lib/say'

const say = sayIn('en')

export default function GapCard({ card, value, setValue, result }) {
  const { words, at, tail, options, answer } = card.gap
  const filled = result ? answer : value
  const markOf = (option) => {
    if (!result) return option.id === value ? 'picked' : undefined
    if (option.id === answer) return 'right'
    return option.id === value ? 'wrong' : undefined
  }
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask">{say('Which word completes it?')}</p>
      <ArabicText as="p" size="lg" className="grow-card-word grow-gap-line">
        {words.slice(0, at).join(' ')}{' '}
        <span className="grow-gap" data-filled={filled ? '' : undefined}>{filled ?? '   '}</span>
        {tail}{' '}{words.slice(at + 1).join(' ')}
      </ArabicText>
      <div className="grow-options grow-options-ar" role="radiogroup" aria-label={say('Words')}>
        {options.map((option) => (
          <button key={option.id} type="button" role="radio" aria-checked={option.id === value} className="grow-option"
            data-mark={markOf(option)} disabled={Boolean(result)} onClick={() => setValue(option.id)}>
            <ArabicText>{option.text}</ArabicText>
          </button>
        ))}
      </div>
    </div>
  )
}
