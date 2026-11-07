import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { surahShares } from '../quiz/coverage'
import { surahCoverageQuery } from '../quiz/quizBanks'
import { useQuizCoverage } from '../quiz/useQuizCoverage'

/**
 * How much of one surah's words this learner knows, as a fraction, the same
 * figure the quiz's per-surah list gives (one query, one cache). Null
 * until something is learnt and the files have come: nothing is guessed.
 */
export function useSurahShare(surah) {
  const { learnt, words, covering } = useQuizCoverage()
  const bySurah = useQuery({ ...surahCoverageQuery, enabled: Boolean(surah) && learnt.length > 0 })
  const one = bySurah.data?.[surah - 1]
  return useMemo(
    () => (one && words.data && covering.data ? surahShares(words.data, covering.data, learnt, [one])[0] : null),
    [one, words.data, covering.data, learnt],
  )
}
