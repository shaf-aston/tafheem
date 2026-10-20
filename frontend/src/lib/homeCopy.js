/** Home's small text helpers: filling {n}-style lines from home.json, the greeting, a progress line. */
import knobs from '../home.json'

const { copy } = knobs

/** `line` with each {key} replaced from `values`. */
export const fill = (line, values) => line.replace(/\{(\w+)\}/g, (_, key) => values[key])

/** The greeting for an hour of day (default: now). */
export function greeting(hour = new Date().getHours()) {
  return (knobs.greetings.find((one) => hour < one.until) ?? knobs.greetings.at(-1)).text
}

/** "N learnt · M answers" for a tab's progress sum, or null when there is none. */
export function progressText(sum) {
  if (!sum) return null
  const answers = fill(sum.attempts === 1 ? copy['answers-one'] : copy['answers-many'], { n: sum.attempts })
  return `${fill(copy.learnt, sum)} · ${answers}`
}
