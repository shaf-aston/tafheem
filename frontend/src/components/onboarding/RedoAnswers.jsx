/**
 * Settings' way back into the first-visit questions: it marks the plan not done (the answers stay, so each screen
 * opens on what was picked) and goes Home, where the questions are asked again. Skip there keeps the old answers.
 */
import config from '../../config/onboarding.json'
import { begun } from '../../lib/learner/plan'
import { usePlan } from '../../lib/learner/usePlan'
import { HOME } from '../../lib/nav/tabs'
import SmallButton from '../ui/buttons/SmallButton'

const { copy } = config

export default function RedoAnswers({ onGo, onClose }) {
  const { plan, save } = usePlan()
  const redo = () => {
    save({ done: false })
    onClose()
    onGo(HOME)
  }
  return (
    <div className="flex flex-wrap items-center gap-3">
      <SmallButton onClick={redo}>{begun(plan) ? copy.redo : copy['redo-first']}</SmallButton>
      <span className="type-small text-[var(--text-faint)]">{copy['redo-hint']}</span>
    </div>
  )
}
