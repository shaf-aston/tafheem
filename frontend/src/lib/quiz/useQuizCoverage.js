import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { coverageOf, learntOf } from './coverage'
import { summaryQuery } from '../learner/record'
import { allWordsQuery, coverageQuery, moduleFor, QUIZ } from './quizBanks'

/**
 * The quiz record, its learnt rows, and how much of the Qur'an they cover.
 * One hook for the quiz insights, the profile and the reader, on one cache, so
 * a new answer or a user switch refreshes all three. The word table is only
 * fetched once something is learnt; `share` is null until then.
 */
export function useQuizCoverage(language = QUIZ.language) {
  const stats = useQuery(summaryQuery(moduleFor(language)))
  const learnt = useMemo(() => learntOf(stats.data), [stats.data])
  const any = learnt.length > 0
  const words = useQuery({ ...allWordsQuery, enabled: any })
  const covering = useQuery({ ...coverageQuery, enabled: any })
  const share = useMemo(
    () => (any && words.data && covering.data ? coverageOf(words.data, covering.data, learnt) : null),
    [any, words.data, covering.data, learnt],
  )
  return { stats, learnt, words, covering, share }
}
