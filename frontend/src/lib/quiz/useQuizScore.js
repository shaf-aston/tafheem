import { useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { recordAttempt } from '../progress'
import { moduleFor } from '../quizBanks'
import { progressKey, useSavedState } from '../stored'
import { useRemembered } from '../useRemembered'

// The running tally, under the learner's own record like the best streak.
const SCORE_KEY = progressKey('quiz-score')
const NO_SCORE = { right: 0, total: 0, streak: 0 }

/**
 * What the Quiz tab's answers add up to: the tally, the best streak ever, and
 * whether answers are reaching the store. `record` is useQuizRound's onAnswer;
 * `clear` empties the tally for a fresh round. `setup` is useQuizSetup's, for
 * filing each answer under what was being tested.
 */
export function useQuizScore(setup) {
  const { language, bankId, groupId, direction } = setup
  const client = useQueryClient()
  // Set once if the store cannot be reached, so a session is never silently
  // saved to nowhere: without it the review list is mysteriously empty later.
  const [saving, setSaving] = useState(true)
  // Kept like the best streak below, so a reload does not wipe the tally; only
  // Start over (or a new word set) does, and Start over in settings forgets it.
  const [saved, setScore] = useSavedState(SCORE_KEY, NO_SCORE)
  const score = useMemo(() => ({ ...NO_SCORE, ...saved }), [saved])
  // The one thing a round leaves behind. Stored as what it is, a number written
  // out, so nothing has to interpret it years later.
  const [best, rememberBest] = useRemembered(progressKey('quiz-best-streak'))
  const bestStreak = Number(best) || 0

  // Everything one answer sets going. Filed and forgotten: the round never waits
  // for the store, and one that is not there costs a row of history rather than
  // the question in front of you. Sent as measured, however long; which timings
  // are honest enough to average is the store's rule, not this tab's.
  const record = ({ question: asked, correct: wasRight, ms }) => {
    recordAttempt({
      module: moduleFor(language),
      item: asked.answerId,
      correct: wasRight,
      ms,
      context: { bank: bankId, group: groupId, direction, word: asked.answerWord },
    }).then((result) => {
      setSaving(result.saved)
      // The answer just changed two numbers on screen: what is owed, on the
      // Review control, and the reading at the foot of the page. Both are
      // re-read; the words of the round being played are not, so the question
      // in front of you cannot change underneath your hand.
      if (result.saved) {
        client.invalidateQueries({ queryKey: ['quiz-review'] })
        client.invalidateQueries({ queryKey: ['quiz-progress'] })
      }
    })

    // One answer, one streak, worked out here rather than inside the state
    // update so that the record it might beat is written once and in the open.
    const streak = wasRight ? score.streak + 1 : 0
    if (streak > bestStreak) rememberBest(String(streak))
    setScore((s) => ({ right: s.right + (wasRight ? 1 : 0), total: s.total + 1, streak }))
  }

  const clear = () => setScore(NO_SCORE)

  return { score, bestStreak, saving, record, clear }
}
