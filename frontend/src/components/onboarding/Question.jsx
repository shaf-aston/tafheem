/**
 * One question of the first visit: its options as big answers (the fact for a pick is the foot's, Onboarding). A multi question
 * (`step.multi`) lets that many be picked, the first counting most; any other takes one. Draws only: the pick is the
 * parent's to keep.
 */
import { fill } from '../../lib/shell/homeCopy'
import ArabicText from '../ui/text/ArabicText'

export default function Question({ step, answer, onPick, copy }) {
  const picked = Array.isArray(answer) ? answer : answer ? [answer] : []
  const hint = step.multi ? (step.hint ?? fill(copy['pick-many'], { n: step.multi })) : null
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{step.tag}</span>
      <h3 className="type-title font-semibold">{step.question}</h3>
      {hint && <p className="grow-card-ask">{hint}</p>}
      <div className="grow-options" role={step.multi ? 'group' : 'radiogroup'} aria-label={step.question}>
        {step.options.map((option) => {
          const on = picked.includes(option.id)
          return (
            <button key={option.id} type="button" role={step.multi ? 'checkbox' : 'radio'} aria-checked={on}
              className="grow-option" data-mark={on ? 'picked' : undefined} onClick={() => onPick(option.id)}>
              {option.arabic && <ArabicText as="span" size="md" className="w-14 shrink-0 text-center">{option.arabic}</ArabicText>}
              <span className="grid min-w-0">
                <span className="font-semibold">{option.label}</span>
                {option.hint && <span className="type-small text-[var(--text-dim)]">{option.hint}</span>}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
