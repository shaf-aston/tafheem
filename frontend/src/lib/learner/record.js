/**
 * The learner's record as the page holds it: every view the store gives of it (one cache entry each, spelt once here),
 * and the one way to file an answer.
 *
 * Which views an answer changes is this module's to know; when a screen re-reads them is the screen's. Filing re-reads
 * at once the overview, which no one plays from and which the learner's level is read from (lib/learner/useLearnerLevel),
 * so "Your Arabic" and Grow's Today follow the answers without a reload. The answered module's own views and the
 * figures beside them are only marked old: a lesson or a round being played holds still, a view opened later reads them
 * afresh, and the screen playing calls `refresh` when it is ready (Grow when a lesson ends, the Quiz after each answer
 * for its Review count). lib/learner/progress.js stays the only code that talks to the store.
 */
import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { fetchAccount, fetchLeaderboard, fetchOverview, fetchReviewItems, fetchSummary, recordAttempt } from './progress'

const RECORD = 'record'

// A module's own views are fresh until an answer marks them old (so a world can tell its record is behind), and are
// re-read when a screen says so (`refresh`), never on coming back to the window: a round or a lesson planned from one
// must not be re-planned behind the player.
const QUIET = { staleTime: Infinity, refetchOnWindowFocus: false }

/** Every item answered in `module`, with its record. */
export const summaryQuery = (module) => ({ queryKey: [RECORD, 'summary', module], queryFn: () => fetchSummary(module), ...QUIET })

/** The items in `module` due for review now, longest-waiting first. */
export const reviewQuery = (module) => ({ queryKey: [RECORD, 'review', module], queryFn: () => fetchReviewItems(module), ...QUIET })

/** Every module answered in, with the streak: an account's, or this device's guest record (docs/plans/2026-10-24-device-guest.md §8). */
export const overviewQuery = (name) => ({ queryKey: [RECORD, 'overview', name], queryFn: fetchOverview, retry: false })

/** The profile's `{ name, joined, answers }`. */
export const accountQuery = (name) => ({ queryKey: [RECORD, 'account', name], queryFn: fetchAccount, enabled: !!name })

/** The global ranking in `module`. */
export const leaderboardQuery = (module) => ({ queryKey: [RECORD, 'leaderboard', module], queryFn: () => fetchLeaderboard(module) })

/** Every module's ranking: for when the learner's place in all of them changes (shown or hidden). */
export const everyRanking = { queryKey: [RECORD, 'leaderboard'] }

/** Re-read now, after an answer: the overview (any module's answer moves it). */
const LIVE = [[RECORD, 'overview']]

/** Marked old, read afresh when next shown: the answered module's views, and the figures any answer adds to. */
const later = (module) => [[RECORD, 'summary', module], [RECORD, 'review', module], [RECORD, 'leaderboard', module], [RECORD, 'account']]

/** Re-read `module`'s own views now: for a screen whose lesson or round has ended. */
const refreshModule = (client, module) => Promise.all(
  [[RECORD, 'summary', module], [RECORD, 'review', module]].map((queryKey) => client.invalidateQueries({ queryKey })),
)

/** File one answer through `client`: resolves recordAttempt's `{ saved, earned }`, never rejects. */
export async function fileAnswer(client, answer) {
  const result = await recordAttempt(answer)
  if (result.saved) {
    for (const queryKey of LIVE) client.invalidateQueries({ queryKey })
    for (const queryKey of later(answer.module)) client.invalidateQueries({ queryKey, refetchType: 'none' })
  }
  return result
}

/** `{ file, refresh }`: file an answer (as `fileAnswer`), and re-read a module's views (as `refreshModule`). */
export function useRecord() {
  const client = useQueryClient()
  const file = useCallback((answer) => fileAnswer(client, answer), [client])
  const refresh = useCallback((module) => refreshModule(client, module), [client])
  return { file, refresh }
}
