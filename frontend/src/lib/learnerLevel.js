/**
 * How much Arabic a learner knows: what they said (`chosen`, '' for nothing yet) until their answers say more.
 * The tiers, their proof modules and the thresholds are levels.json's; this file is only the rule, kept pure so
 * it can be tested on its own. The learner's answers come from the progress overview (one row per module).
 */
import config from '../levels.json'

/** The levels.json numbers this rule reads, by the names the code uses. */
export const RULES = {
  levels: config.levels,
  minAnswers: config['min-answers'],
  pass: config.pass,
  fail: config.fail,
}

export const LEVELS = config.levels
export const LEVEL_IDS = LEVELS.map((level) => level.id)
export const LEVEL_KEY = config['storage-key']
export const LEVEL_COPY = config.copy
export const levelOf = (id) => LEVELS.find((level) => level.id === id) ?? null

/** One tier's answers over its proof modules: how many, and the share right. */
function tally(proof, modules) {
  const rows = modules.filter((row) => proof.includes(row.module))
  const answers = rows.reduce((sum, row) => sum + row.attempts, 0)
  const right = rows.reduce((sum, row) => sum + row.correct, 0)
  return { answers, share: answers ? right / answers : 0 }
}

/**
 * The level the learner is at: `{ level, settled, basis }`.
 *
 * Not settled (no tier has `minAnswers` answers yet): the chosen level, which the learner may still change.
 * Settled: at least the chosen level, the highest tier held, and one past the highest tier passed; but never
 * above the lowest tier struggled with. `basis` is the tier whose answers decided it, for saying why.
 */
export function classify(chosen, modules = [], rules = RULES) {
  const { levels, minAnswers, pass, fail } = rules
  const tiers = levels
    .map((level, at) => ({ id: level.id, at, ...tally(level.proof, modules) }))
    .filter((tier) => tier.answers >= minAnswers)
  if (!tiers.length) return { level: chosen, settled: false, basis: null }

  const top = levels.length - 1
  const struggled = tiers.filter((tier) => tier.share < fail)
  const held = tiers.filter((tier) => tier.share >= fail)
  const passed = held.filter((tier) => tier.share >= pass)

  // Each candidate floor with the tier that gave it; the highest wins, the learner's own word first on a tie.
  const floors = [
    { at: levels.findIndex((level) => level.id === chosen), tier: null },
    ...held.map((tier) => ({ at: tier.at, tier })),
    ...passed.map((tier) => ({ at: Math.min(tier.at + 1, top), tier })),
  ]
  const floor = floors.reduce((best, one) => (one.at > best.at ? one : best), { at: 0, tier: null })
  const ceiling = struggled[0]
  const capped = ceiling && ceiling.at < floor.at
  const decided = capped ? ceiling : floor.tier ?? tiers[0]
  return {
    level: levels[capped ? ceiling.at : floor.at].id,
    settled: true,
    basis: { id: decided.id, answers: decided.answers, share: decided.share },
  }
}
