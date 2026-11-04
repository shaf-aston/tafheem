/**
 * Home's first visit: a short run of questions in the lesson's own look (one idea a screen, a bar, one button at the
 * foot), a true fact after each pick, then the plan. Back keeps every answer (they are saved as they are given), and
 * Skip is always there: it only marks the run done, so Home falls back to the three-level picker. Starting writes
 * what was said where the rest of the app reads it: the level (lib/learner/useLearnerLevel.js), the daily goal
 * (Grow's home) and the plan itself (lib/learner/usePlan.js), and opens the level's first place.
 * The order and the rules are lib/learner/flow.js and plan.js; the words are config/onboarding.json.
 */
import { useState } from 'react'

import config from '../../config/onboarding.json'
import { screensOf, answered, rightOf } from '../../lib/learner/flow'
import { levelOf } from '../../lib/learner/learnerLevel'
import { factOf, goalXpOf, levelIdOf, levelOf as levelNumberOf } from '../../lib/learner/plan'
import { GOALS, GOAL_KEY } from '../../lib/learner/rewards'
import { getProfile } from '../../lib/learner/profile'
import { useLearnerLevel } from '../../lib/learner/useLearnerLevel'
import { usePlan } from '../../lib/learner/usePlan'
import { writeRaw } from '../../lib/store/stored'
import PrimaryButton from '../ui/buttons/PrimaryButton'
import Fact from './Fact'
import PlanReady from './PlanReady'
import Question from './Question'
import Tap from './Tap'

const { copy } = config
const ACCENT = 'var(--primary)'

export default function Onboarding({ onGo }) {
  const { plan, save } = usePlan()
  const { choose } = useLearnerLevel()
  const [at, setAt] = useState(0)
  const [taps, setTaps] = useState([])
  const screens = screensOf(plan)
  const last = screens.length - 1
  const here = Math.min(at, last)
  const screen = screens[here]
  // The fact for the first pick, in the foot beside the button, so it is in view whatever the length of the options.
  const picked = screen.kind === 'step' ? [plan[screen.step.id]].flat()[0] : null
  const fact = picked ? factOf(screen.step, picked) : null

  const pick = (step, id) => {
    if (!step.multi) return save({ [step.id]: id })
    const was = plan[step.id]
    save({ [step.id]: was.includes(id) ? was.filter((one) => one !== id) : was.length < step.multi ? [...was, id] : was })
  }
  const tap = (index, option) => setTaps((was) => { const next = [...was]; next[index] = option; return next })
  const forward = () => {
    if (screen.kind === 'tap' && screen.index === screen.step.items.length - 1) save({ check: rightOf(screen.step, taps), keepSaid: false })
    setAt(here + 1)
  }
  const finish = () => {
    const level = levelIdOf(plan)
    if (level) choose(level)
    const xp = String(goalXpOf(plan))
    if (GOALS.includes(xp)) writeRaw(GOAL_KEY, xp)
    save({ done: true })
    onGo(...levelOf(level).start)
  }
  // The level the other way, when the check and what was said disagree.
  const other = () => {
    if (plan.check === null || plan.know === null) return null
    const flipped = levelNumberOf({ ...plan, keepSaid: !plan.keepSaid })
    return flipped === levelNumberOf(plan) ? null : { id: levelIdOf({ ...plan, keepSaid: !plan.keepSaid }), said: !plan.keepSaid }
  }

  return (
    <section className="grow-lesson" style={{ '--w': ACCENT }} aria-label={copy.label}>
      <div className="grow-lesson-top">
        <button type="button" className="grow-x" aria-label={copy.back} disabled={here === 0} onClick={() => setAt(here - 1)}>
          <span aria-hidden="true">‹</span>
        </button>
        <span className="grow-lesson-bar" role="progressbar" aria-valuemin={0} aria-valuemax={last} aria-valuenow={here} aria-label={copy.label}>
          <i style={{ width: `${(100 * here) / last}%` }} />
        </span>
        <button type="button" className="type-small text-[var(--text-dim)] px-2 min-h-11" onClick={() => save({ done: true })}>{copy.skip}</button>
      </div>

      <div className="grow-lesson-card">
        {screen.kind === 'step' && <Question key={screen.id} step={screen.step} answer={plan[screen.step.id]} onPick={(id) => pick(screen.step, id)} copy={copy} />}
        {screen.kind === 'tap' && <Tap key={screen.id} step={screen.step} index={screen.index} picked={taps[screen.index]} onPick={(option) => tap(screen.index, option)} copy={copy} />}
        {screen.kind === 'ready' && <PlanReady plan={plan} other={other()} guest={!getProfile()} copy={copy} onSwitch={() => save({ keepSaid: !plan.keepSaid })} />}
      </div>

      <div className="grow-lesson-foot bg-[var(--bg)]">
        {fact && <Fact fact={fact} />}
        {screen.kind === 'ready'
          ? <PrimaryButton accent={ACCENT} onClick={finish}>{copy['ready-start']}</PrimaryButton>
          : <PrimaryButton accent={ACCENT} disabled={!answered(screen, plan, taps)} onClick={forward}>{copy.continue}</PrimaryButton>}
      </div>
    </section>
  )
}
