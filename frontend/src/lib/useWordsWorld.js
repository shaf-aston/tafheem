/**
 * The Words world's data: the word set it walks through, what this learner has
 * answered in it, and a fresh lesson on demand.
 *
 * The record is the Quiz tab's own (module 'quiz', one row per meaning), read
 * from the server's summary, so a word learnt in either place counts in both
 * and the review timer is the one the Quiz's Review already uses. Grow asks in
 * English, the quiz's default; the quiz's other languages keep their own record.
 */
import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import config from '../worlds.json'
import { cardsOf, lessonWords, stageOf } from './lesson'
import { fetchSummary } from './progress'
import { MODULE, allWords, wordsFor } from './quizBanks'

const { lesson: LESSON, stages: STAGES } = config

export function useWordsWorld() {
  const client = useQueryClient()
  const words = useQuery({
    queryKey: ['grow-words', LESSON.bank],
    queryFn: async () => ({ order: await wordsFor(LESSON.bank), all: await allWords() }),
    staleTime: Infinity,
  })
  const summary = useQuery({ queryKey: ['grow-summary', MODULE], queryFn: () => fetchSummary(MODULE) })

  const state = useMemo(() => {
    if (!words.data || !summary.data) return null
    const { order } = words.data
    const inSet = new Set(order.map((word) => word.meaningKey))
    const items = summary.data
    const seen = new Set(items.map((row) => row.item))
    const due = items.filter((row) => row.due).sort((a, b) => a.dueAt.localeCompare(b.dueAt)).map((row) => row.item)
    const learnt = items.filter((row) => row.known && inSet.has(row.item)).length
    const next = lessonWords({ ...words.data, seen, due, fresh: LESSON.new, most: LESSON['most-new'], size: LESSON.size })
    return {
      seen, due, learnt, next,
      fresh: order.filter((word) => !seen.has(word.meaningKey)).length,
      stage: stageOf(learnt, STAGES),
    }
  }, [words.data, summary.data])

  // The words are picked when the record is read; the questions are drawn fresh each time.
  const makeLesson = (random = Math.random) => cardsOf(state.next, words.data.all, random)

  // After a lesson the record has moved: re-read it here and wherever the Quiz shows it.
  const refresh = () => {
    client.invalidateQueries({ queryKey: ['grow-summary'] })
    client.invalidateQueries({ queryKey: ['quiz-review'] })
    client.invalidateQueries({ queryKey: ['quiz-progress'] })
  }

  return {
    module: MODULE,
    stages: STAGES,
    ready: Boolean(state),
    error: words.error ?? summary.error,
    retry: () => { words.refetch(); summary.refetch() },
    ...(state ?? {}),
    dueCount: state?.due.length ?? 0,
    makeLesson,
    refresh,
  }
}
