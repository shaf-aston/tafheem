import { useMemo } from 'react'

import { learntLemmas } from './coverage'
import { useQuizCoverage } from './useQuizCoverage'

const NONE = new Set()

/** The Qur'an lemmas this learner has learnt, for marking words in the reader. */
export function useLearntLemmas() {
  const { learnt, words, covering } = useQuizCoverage()
  return useMemo(
    () => (learnt.length && words.data && covering.data ? learntLemmas(words.data, covering.data, learnt) : NONE),
    [learnt, words.data, covering.data],
  )
}
