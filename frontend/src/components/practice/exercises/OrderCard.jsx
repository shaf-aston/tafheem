/** Tap the steps in order; tap a placed step to take it back. Once checked, each place shows right or wrong. */
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function OrderCard({ card, value, setValue, result }) {
  const placed = value ?? []
  const left = card.deck.filter((step) => !placed.includes(step))
  const markOf = (step, i) => (result ? (card.steps[i] === step ? 'right' : 'wrong') : 'picked')
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask grow-ask-strong">{card.ask}</p>
      <ol className="grow-order" aria-label={say('Your order')}>
        {card.steps.map((_, i) => (
          <li key={i} className="grow-order-slot">
            <span className="grow-order-n" aria-hidden="true">{i + 1}</span>
            {placed[i] ? (
              <button type="button" className="grow-option grow-order-step" data-mark={markOf(placed[i], i)} disabled={Boolean(result)}
                aria-label={say('Take back {step}', { step: placed[i] })} onClick={() => setValue(placed.filter((step) => step !== placed[i]))}>
                {placed[i]}
              </button>
            ) : <span className="grow-order-empty" />}
          </li>
        ))}
      </ol>
      {!result && (
        <div className="grow-order-deck">
          {left.map((step) => (
            <button key={step} type="button" className="grow-option grow-order-step" onClick={() => setValue([...placed, step])}>{step}</button>
          ))}
        </div>
      )}
    </div>
  )
}
