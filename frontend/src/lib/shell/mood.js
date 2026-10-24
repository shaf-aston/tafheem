/**
 * Turns what the app already knows into one word for the mascot to wear.
 *
 * Pure on purpose: the mascot holds no state of its own, so it can never drift
 * out of step with the thing it is describing. Callers pass what they already
 * have, the pending flag, the health check, the quiz score; and get a mood.
 */
import { streakAt } from './mascot'

/**
 * @param offline the backend health check has failed
 * @param busy    a request is in flight
 * @param streak  how many quiz answers are right in a row
 * @param answer  'correct' | 'wrong' for the question just answered, else null
 */
export function moodFrom({ offline = false, busy = false, streak = 0, answer = null } = {}) {
  // A just-answered question wins: it is the most recent thing that happened.
  if (answer === 'correct' || answer === 'wrong') return answer
  if (offline) return 'offline'
  if (busy) return 'thinking'
  if (streak >= streakAt) return 'streak'
  return 'idle'
}
