/**
 * Where the Tamreen drill keeps what you have picked and checked, and the one
 * way to forget it.
 *
 * Its own file so the header's Start over can clear it (lib/journey.js) without
 * pulling in the whole practise panel: one module owns the key, so nothing else
 * has to know the shape of what is saved.
 */
import { useEffect, useState } from 'react'

import { forgetKey, readSaved, writeSaved } from './stored'

const ANSWERS_KEY = 'tamreen-answers'

/** Every pick and check, saved as { id: { picks, checked } } so a reload keeps them. */
export function useAnswers() {
  const [answers, setAnswers] = useState(() => readSaved(ANSWERS_KEY, {}))
  useEffect(() => { writeSaved(ANSWERS_KEY, answers) }, [answers])
  return [answers, setAnswers]
}

/** Forget every Tamreen answer. The page reloads after this, so no state to clear. */
export function forgetTamreenAnswers() {
  forgetKey(ANSWERS_KEY)
}
