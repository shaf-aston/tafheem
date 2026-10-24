/**
 * Where the Tamreen drill keeps what you have picked and checked. Kept under
 * progressKey, so Start over forgets it with the rest of the learner's record.
 */
import { progressKey, useSavedState } from '../store/stored'

const ANSWERS_KEY = progressKey('tamreen-answers')

/** Every pick and check, saved as { id: { picks, checked } } so a reload keeps them. */
export function useAnswers() {
  return useSavedState(ANSWERS_KEY, {})
}
