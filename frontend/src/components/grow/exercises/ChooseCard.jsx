/** One answer from a few: a case to judge, or a gap in the book's sentence (`ar` with ____). */
import ArabicText from '../../ui/ArabicText'
import Bayt from '../../ui/Bayt'
import { hemistichs } from '../../../lib/text/verse'
import OneOf from './OneOf'
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function ChooseCard({ card, value, setValue, result }) {
  const filled = result ? card.options.find((option) => option.id === card.answer)?.text : card.options.find((option) => option.id === value)?.text
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
      <OneOf options={card.options} answer={card.answer} value={value} setValue={setValue} result={result} arabic={card.arabic} label={say('Answers')} />
    </div>
  )
}
