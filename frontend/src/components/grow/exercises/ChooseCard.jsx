/** One answer from a few: a case to judge, or a gap in the book's sentence (`ar` with ____). */
import ArabicText from '../../ui/ArabicText'
import { sayIn } from '../../../lib/say'

const say = sayIn('en')

export default function ChooseCard({ card, value, setValue, result }) {
  const filled = result ? card.options.find((option) => option.id === card.answer)?.text : card.options.find((option) => option.id === value)?.text
  const markOf = (option) => {
    if (!result) return option.id === value ? 'picked' : undefined
    if (option.id === card.answer) return 'right'
    return option.id === value ? 'wrong' : undefined
  }
  const [before, after] = card.ar?.split('____') ?? []
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask grow-ask-strong">{card.ask}</p>
      {card.ar && (
        <ArabicText as="p" className="grow-rule-ar">
          {after === undefined ? card.ar : (
            <>{before}<span className="grow-gap" data-filled={filled ? '' : undefined}>{filled ?? '   '}</span>{after}</>
          )}
        </ArabicText>
      )}
      <div className={card.arabic ? 'grow-options grow-options-ar' : 'grow-options'} role="radiogroup" aria-label={say('Answers')}>
        {card.options.map((option) => (
          <button key={option.id} type="button" role="radio" aria-checked={option.id === value} className="grow-option"
            data-mark={markOf(option)} disabled={Boolean(result)} onClick={() => setValue(option.id)}>
            {card.arabic ? <ArabicText>{option.text}</ArabicText> : option.text}
          </button>
        ))}
      </div>
    </div>
  )
}
