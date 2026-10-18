/** Every one that fits: tap to pick or unpick, then Check. Once checked, the right ones show green and a wrong pick red. */
import { sayIn } from '../../../lib/say'

const say = sayIn('en')

export default function PickCard({ card, value, setValue, result }) {
  const picked = new Set(value ?? [])
  const rights = card.options.filter((option) => option.right).length
  const toggle = (id) => {
    const next = new Set(picked)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setValue([...next])
  }
  const markOf = (option) => {
    if (!result) return picked.has(option.id) ? 'picked' : undefined
    if (option.right) return 'right'
    return picked.has(option.id) ? 'wrong' : undefined
  }
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask grow-ask-strong">{card.ask}</p>
      <p className="grow-card-ask">{rights === 1 ? say('Pick the one that fits.') : say('Pick the {n} that fit.', { n: rights })}</p>
      <div className="grow-options" role="group" aria-label={say('Answers')}>
        {card.options.map((option) => (
          <button key={option.id} type="button" aria-pressed={picked.has(option.id)} className="grow-option grow-option-check"
            data-mark={markOf(option)} disabled={Boolean(result)} onClick={() => toggle(option.id)}>
            {option.text}
          </button>
        ))}
      </div>
    </div>
  )
}
