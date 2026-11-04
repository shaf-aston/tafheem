/**
 * What to offer this learner first, across Grow's worlds and the tabs that teach (Colloquial, Memorise, ...): the one
 * ranking Home and Grow both read, so they never disagree. Pure maths, no AI. The places, weights and knobs are
 * onboarding.json's `places` and `rank`.
 *
 *   score = (goal + level) × fade + done
 *
 * goal and level are what the learner said (lib/learner/plan.js): how much a place serves the goals they picked, and
 * how well it fits the level they gave. done is what they have actually been doing, the recent use Grow's own
 * suggestion already counts (lib/grow/suggest.js). fade shrinks what was said as answers come in, so after a few
 * weeks the record leads and the survey only breaks ties.
 */
import config from '../../config/onboarding.json'
import { ofWorld, recentOf, usageOf } from '../grow/suggest'
import { worldOf } from '../grow/worlds'
import { tabOf } from '../nav/moduleTab'
import { levelOf, matches } from './plan'

export const PLACES = config.places
export const RANK = config.rank

/** How well a place suits `level`: inside its band 1, one step out `near-level`, further 0; any while unknown. */
function fitOf(place, level, k) {
  if (level === null) return 1
  const [low, high] = place.band
  const off = level < low ? low - level : level > high ? level - high : 0
  return off === 0 ? 1 : off === 1 ? k['near-level'] : 0
}

/** How much a place serves the picked goals, the first in full; then its `times` that hold. */
function goalOf(place, plan, k) {
  if (!plan.goals.length) return { goal: k['no-goal'][place.id] ?? 0, served: null, lowered: false }
  const goal = plan.goals.reduce((sum, id, at) => sum + (place.goals[id] ?? 0) * (at ? k['second-goal'] : 1), 0)
  const by = (place.times ?? []).filter((one) => matches(one.when, plan)).reduce((product, one) => product * one.by, 1)
  return { goal: goal * by, served: plan.goals.find((id) => place.goals[id]) ?? null, lowered: by < 1 }
}

/** Whether a module row is this place's: a world's record, or any record its tab files under. */
const belongsTo = (place) => (place.world ? ofWorld(worldOf(place.world)) : (module) => tabOf(module)?.id === place.tab)

/** A place still on offer: a tab, or a live world. */
const open = (place) => !place.world || worldOf(place.world)?.live

/**
 * Every place worth offering, best first: `{ place, score, parts: { goal, level, done }, why }`. `why` says what
 * put it there: `goal` (the picked goal it serves, or null), `level` (it fits the level said), `done` (it has been
 * practised lately), `lowered` (an answer pushed it down, a Hanafi book for a Shafiʿi). Ties keep onboarding.json order.
 */
export function recommend(plan, modules = [], now = Date.now(), k = RANK) {
  const level = levelOf(plan)
  const answers = modules.reduce((sum, row) => sum + row.attempts, 0)
  const fade = 1 / (1 + answers / k['fade-at'])
  return PLACES.filter(open)
    .map((place, at) => {
      const fit = fitOf(place, level, k)
      const { goal, served, lowered } = goalOf(place, plan, k)
      const parts = {
        goal: goal * fit * fade,
        level: goal > 0 ? k['level-weight'] * fit * fade : 0,
        done: recentOf(usageOf(belongsTo(place), modules), now) * k['done-weight'],
      }
      const why = { goal: served, level: level !== null && parts.level > 0, done: parts.done > 0, lowered }
      return { place, at, score: parts.goal + parts.level + parts.done, parts, why }
    })
    .filter((one) => one.score > 0)
    .sort((a, b) => b.score - a.score || a.at - b.at)
}
