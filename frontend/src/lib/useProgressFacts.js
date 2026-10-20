import { useQuery } from '@tanstack/react-query'

import { shareOf } from './coverage'
import { fetchAccount, fetchOverview } from './progress'
import { MEANINGS } from './quiz'
import { moduleFor, QUIZ } from './quizBanks'
import { useQuizCoverage } from './useQuizCoverage'
import { useRemembered } from './useRemembered'
import { useRewards } from './useRewards'

/**
 * A logged-in learner's figures, read the one way the profile and Home's progress
 * column both show them, on one cache: the account, the overview (streak), XP,
 * the words learnt and how much of the Qur'an they cover. Words are counted in
 * the language the quiz was last set to, so an Urdu learner's are filed under
 * the Urdu module, not the default's.
 */
export function useProgressFacts(name) {
  const [language] = useRemembered('quiz-language', Object.keys(MEANINGS), QUIZ.language)
  const module = moduleFor(language)
  const account = useQuery({ queryKey: ['account', name], queryFn: fetchAccount, enabled: !!name })
  const overview = useQuery({ queryKey: ['overview', name], queryFn: fetchOverview, enabled: !!name })
  const { stats, learnt, share } = useQuizCoverage(language)
  const { rewards, gain } = useRewards(name)
  // Nothing learnt covers nothing; something learnt waits for the word table.
  const covered = !stats.data ? null : learnt.length === 0 ? '0%' : share === null ? null : `${shareOf(share, language)}%`
  return { module, account, overview, stats, learnt, covered, rewards, gain }
}
