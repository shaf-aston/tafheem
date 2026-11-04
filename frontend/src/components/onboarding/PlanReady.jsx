/**
 * The last screen: the plan in three lines (where you start, the daily goal, the first stops), a way to take the level
 * you said over the check's (or back), and a log-in for a guest. The first stops are recommend()'s top places.
 */
import { levelOf } from '../../lib/learner/learnerLevel'
import { goalXpOf, levelIdOf } from '../../lib/learner/plan'
import { recommend } from '../../lib/learner/recommend'
import { fill } from '../../lib/shell/homeCopy'
import { worldOf } from '../../lib/grow/worlds'
import { LISTED } from '../../lib/nav/tabs'
import LogInButton from '../profile/LogInButton'

const FIRST_STOPS = 3
const nameOf = (place) => (place.world ? worldOf(place.world)?.name : LISTED.find((tab) => tab.id === place.tab)?.label)

/** The level the other way (the one the learner did not get), for the switch: null when there is no other. */
export default function PlanReady({ plan, other, guest, onSwitch, copy }) {
  const level = levelOf(levelIdOf(plan))
  const xp = goalXpOf(plan)
  const stops = recommend(plan).slice(0, FIRST_STOPS)
  const instead = other && levelOf(other.id)
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{copy.label}</span>
      <h3 className="type-title font-semibold">{copy['ready-title']}</h3>
      <dl className="grid gap-3">
        {[
          [copy['ready-level'], level.title],
          xp && [copy['ready-goal'], fill(copy['ready-goal-line'], { xp, minutes: plan.minutes })],
          [copy['ready-picks'], stops.map((one) => nameOf(one.place)).filter(Boolean).join(' · ')],
        ].filter(Boolean).map(([label, value]) => (
          <div key={label} className="grid gap-0.5 rounded-[var(--radius-md)] border border-[var(--border-hi)] bg-[var(--surface)] px-4 py-3">
            <dt className="type-small text-[var(--text-dim)]">{label}</dt>
            <dd className="font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
      {instead && (
        <button type="button" className="grow-done-back" onClick={onSwitch}>
          {fill(copy[other.said ? 'ready-switch-said' : 'ready-switch-check'], { level: instead.title })}
        </button>
      )}
      {guest && (
        <p className="flex flex-wrap items-center gap-x-3 gap-y-2 text-[var(--text-dim)]">
          <span>{copy['ready-login']}</span>
          <LogInButton>{copy['ready-login-go']}</LogInButton>
        </p>
      )}
    </div>
  )
}
