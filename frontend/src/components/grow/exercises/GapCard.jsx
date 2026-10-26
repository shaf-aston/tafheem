/** Complete the hadith: its key line with one word blanked, four words to choose from. */
import ArabicText from '../../ui/ArabicText'
import OneOf from './OneOf'
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function GapCard({ card, value, setValue, result }) {
  const { words, at, tail, options, answer } = card.gap
  const filled = result ? answer : value
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask">{say('Which word completes it?')}</p>
      <ArabicText as="p" size="lg" className="grow-card-word grow-gap-line">
        {words.slice(0, at).join(' ')}{' '}
        <span className="grow-gap" data-filled={filled ? '' : undefined}>{filled ?? '   '}</span>
        {tail}{' '}{words.slice(at + 1).join(' ')}
      </ArabicText>
      <OneOf options={options} answer={answer} value={value} setValue={setValue} result={result} arabic label={say('Words')} />
    </div>
  )
}
