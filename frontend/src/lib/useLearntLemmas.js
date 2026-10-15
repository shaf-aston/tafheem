import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { learntLemmas, learntOf } from './coverage'
import { allWordsQuery, coverageQuery, progressQuery, QUIZ } from './quizBanks'

const NONE = new Set()

/**
 * The Qur'an lemmas this learner has learnt, for marking words in the reader.
 * Same cache as the quiz insights, so a new answer or a name switch refreshes
 * both. The word table is only fetched once something is learnt.
 */
export function useLearntLemmas() {
  const language = QUIZ.language
  const stats = useQuery(progressQuery(language))
  const learnt = useMemo(() => learntOf(stats.data), [stats.data])
  const any = learnt.length > 0
  const words = useQuery({ ...allWordsQuery, enabled: any })
  const covering = useQuery({ ...coverageQuery, enabled: any })
  return useMemo(
    () => (any && words.data && covering.data ? learntLemmas(words.data, covering.data, learnt) : NONE),
    [any, words.data, covering.data, learnt],
  )
}
