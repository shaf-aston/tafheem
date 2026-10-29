/**
 * The screens of the first visit, in order, for a plan: a question each, the placement's taps one each, then the
 * plan itself. Pure, so the order (and which branches are skipped) tests on its own; components/onboarding/ only draws.
 */
import { visibleSteps } from './plan'

/** `{ id, kind: 'step' | 'tap' | 'ready', step?, index? }` for each screen; `index` is the tap's item. */
export function screensOf(plan) {
  const asked = visibleSteps(plan).flatMap((step) =>
    step.items
      ? step.items.map((item, index) => ({ id: `${step.id}-${index}`, kind: 'tap', step, index }))
      : [{ id: step.id, kind: 'step', step }])
  return [...asked, { id: 'ready', kind: 'ready' }]
}

/** Whether the screen can be left forward: a question needs an answer (a multi one, at least one), a tap a pick. */
export function answered(screen, plan, taps) {
  if (screen.kind === 'ready') return true
  if (screen.kind === 'tap') return taps[screen.index] !== undefined
  const answer = plan[screen.step.id]
  return Array.isArray(answer) ? answer.length > 0 : answer !== null
}

/** How many of the placement's taps were right. */
export const rightOf = (step, taps) => step.items.filter((item, at) => taps[at] === item.right).length
