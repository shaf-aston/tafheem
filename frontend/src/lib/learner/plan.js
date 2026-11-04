/**
 * The first-visit answers, as a plan: what the learner said about why, how much and how long. The questions and
 * their options are onboarding.json's; this file is only the rules, kept pure so they test on their own.
 *
 * A stored plan is untrusted (it outlives config changes, and a person can edit it by hand), so it is always read
 * through readPlan: an option no longer offered is dropped, and so is the answer to a question no longer asked
 * (a dialect, once "speak" is unpicked). What is left is all the ranking (lib/learner/recommend.js) ever sees.
 */
import config from '../../config/onboarding.json'
import { LEVEL_IDS } from './learnerLevel'

export const PLAN_KEY = config['storage-key']
export const STEPS = config.steps
export const LEVELS = config.levels

const CHECK = STEPS.find((step) => step.items)

/** Nothing answered yet. `check`: how many of the placement taps were right, null if not taken; `keepSaid`: the
 *  learner kept the level they said over the check's; `done`: finished or skipped, so it is not asked again. */
export const EMPTY = Object.freeze({
  ...Object.fromEntries(STEPS.filter((step) => !step.items).map((step) => [step.id, step.multi ? [] : null])),
  check: null,
  keepSaid: false,
  done: false,
})

/** Whether every answer named in `when` is one of its listed ids; for a multi answer, whether any picked one is. */
export function matches(when, plan) {
  return Object.entries(when ?? {}).every(([id, allowed]) => {
    const answer = plan[id]
    return Array.isArray(answer) ? answer.some((one) => allowed.includes(one)) : allowed.includes(answer)
  })
}

/** The questions this plan is asked, in order: a branch whose `when` does not hold is left out. */
export const visibleSteps = (plan) => STEPS.filter((step) => matches(step.when, plan))

const offered = (step) => step.options.map((option) => option.id)

function parse(raw) {
  if (raw && typeof raw === 'object') return raw
  try {
    const value = JSON.parse(raw)
    return value && typeof value === 'object' ? value : {}
  } catch {
    return {}
  }
}

/** A stored plan (its text, or the object) made safe: only offered options, only asked questions. */
export function readPlan(raw) {
  const given = parse(raw)
  const plan = { ...EMPTY }
  // In step order, so a branch is judged on answers already cleaned.
  for (const step of STEPS) {
    if (!matches(step.when, plan)) continue
    if (step.items) {
      const right = given.check
      if (Number.isInteger(right) && right >= 0 && right <= step.items.length) plan.check = right
      plan.keepSaid = plan.check !== null && given.keepSaid === true
    } else if (step.multi) {
      const picked = Array.isArray(given[step.id]) ? given[step.id] : []
      plan[step.id] = [...new Set(picked.filter((id) => offered(step).includes(id)))].slice(0, step.multi)
    } else if (offered(step).includes(given[step.id])) {
      plan[step.id] = given[step.id]
    }
  }
  plan.done = given.done === true
  return plan
}

/** The plan as it is stored. */
export const writePlan = (plan) => JSON.stringify(readPlan(plan))

/**
 * The level answered, 0 (cannot read the letters yet) to 3, or null before it is answered. Not reading is 0 whatever
 * else was said; then a check taken, unless the learner kept what they said; then what they said.
 */
export function levelOf(plan) {
  const fromRead = LEVELS.read[plan.read]
  if (fromRead !== undefined) return fromRead
  if (plan.check !== null && !plan.keepSaid) return CHECK.levels[plan.check]
  return LEVELS.know[plan.know] ?? null
}

/** The levels.json level this plan starts at (not reading starts at the first), or null before it is answered. */
export function levelIdOf(plan) {
  const level = levelOf(plan)
  return level === null ? null : LEVEL_IDS[Math.max(level, 1) - 1]
}

/** The daily XP goal the picked minutes stand for, or null. */
export function goalXpOf(plan) {
  return STEPS.find((step) => step.id === 'minutes').options.find((option) => option.id === plan.minutes)?.xp ?? null
}

/** The fact shown after picking `id` in `step`: its own, else the step's `*`, else null. */
export const factOf = (step, id) => step.fact?.[id] ?? step.fact?.['*'] ?? null
