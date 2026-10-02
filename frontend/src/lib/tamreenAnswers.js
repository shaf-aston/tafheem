/**
 * Where the Tamreen drill keeps what you have picked and checked. Kept under
 * progressKey, so Start over forgets it with the rest of the learner's record.
 */
import { useEffect, useState } from 'react'

import { progressKey, readSaved, writeSaved } from './stored'

const ANSWERS_KEY = progressKey('tamreen-answers')

/** Every pick and check, saved as { id: { picks, checked } } so a reload keeps them. */
export function useAnswers() {
  const [answers, setAnswers] = useState(() => readSaved(ANSWERS_KEY, {}))
  useEffect(() => { writeSaved(ANSWERS_KEY, answers) }, [answers])
  return [answers, setAnswers]
}
