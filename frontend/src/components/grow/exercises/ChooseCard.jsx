/** One answer from a few: a case to judge, or a gap in the book's sentence (`ar` with ____). */
import ArabicText from '../../ui/ArabicText'
import Bayt from '../../ui/Bayt'
import { hemistichs } from '../../../lib/text/verse'
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function ChooseCard({ card, value, setValue, result }) {
  const filled = result ? card.options.find((option) => option.id === card.answer)?.text : card.options.find((option) => option.id === value)?.text
  const markOf = (option) => {
    if (!result) return option.id === value ? 'picked' : undefined
    if (option.id === card.answer) return 'right'
    return option.id === value ? 'wrong' : undefined
  }
  // The gap sits in one half of a bayt, so the halves are split first and only then the blank.
  const gapped = (text) => {
    const [before, after] = text.split('____')
    return after === undefined ? text : <>{before}<span className="grow-gap" data-filled={filled ? '' : undefined}>{filled ?? '   '}</span>{after}</>
  }
  const halves = card.ar ? hemistichs(card.ar) : []
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask grow-ask-strong">{card.ask}</p>
      {card.ar && (
        <ArabicText as="p" className="grow-rule-ar">
          {halves.length > 1 ? <Bayt halves={halves.map(gapped)} /> : gapped(card.ar)}
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
