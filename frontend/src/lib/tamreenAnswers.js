/**
 * Where the Tamreen drill keeps what you have picked and checked, and the one
 * way to forget it.
 *
 * Its own file so the header's Start over can clear it (lib/journey.js) without
 * pulling in the whole practise panel: one module owns the key, so nothing else
 * has to know the shape of what is saved.
 */
import { useEffect, useState } from 'react'

const ANSWERS_KEY = 'tamreen-answers'

/** Every pick and check, saved as { id: { picks, checked } } so a reload keeps them. */
export function useAnswers() {
  const [answers, setAnswers] = useState(() => {
    try { return JSON.parse(localStorage.getItem(ANSWERS_KEY) || '{}') } catch { return {} }
  })
  useEffect(() => {
    try { localStorage.setItem(ANSWERS_KEY, JSON.stringify(answers)) } catch { /* private browsing, kept for this visit */ }
  }, [answers])
  return [answers, setAnswers]
}

/** Forget every Tamreen answer. The page reloads after this, so no state to clear. */
export function forgetTamreenAnswers() {
  try { localStorage.removeItem(ANSWERS_KEY) } catch { /* nothing saved to forget */ }
}
