/**
 * The Words world's data: its word set, the learner's record, a lesson on demand.
 * The record is the Quiz's own (module 'quiz', English), so both tabs share it.
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

  const makeLesson = (random = Math.random) => cardsOf(state.next, words.data.all, random)

  // After a lesson: re-read here and in the Quiz.
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
