/**
 * A book world's data (Fiqh: public/grow/quduri.json): the book, the learner's record for its `module`, each lesson's
 * status, the next lesson, what is due, and a lesson's cards on demand. Rules: lib/bookLesson.js; entry: worlds.json.
 */
import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { lessonCards, partsOf, reviewCards } from './bookLesson'
import { fetchSummary } from './progress'

/** The lesson id a review goes by, in the address and to `makeLesson`. */
export const REVIEW = 'review'

async function load(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Could not load the book (${response.status})`)
  return response.json()
}

export function useBookWorld(world) {
  const client = useQueryClient()
  const source = useQuery({ queryKey: ['grow-source', world.id], queryFn: () => load(world.source), staleTime: Infinity })
  const summary = useQuery({ queryKey: ['grow-summary', world.module], queryFn: () => fetchSummary(world.module) })
  const state = useMemo(() => (source.data && summary.data ? partsOf(source.data, summary.data) : null), [source.data, summary.data])

  return {
    world,
    ready: Boolean(state),
    error: source.error ?? summary.error,
    retry: () => { source.refetch(); summary.refetch() },
    book: source.data,
    ...(state ?? { parts: [], areas: [], next: null, due: [] }),
    // A lesson's cards, or the due ones for REVIEW; null when there is no such lesson.
    makeLesson: (lessonId, random = Math.random) => (lessonId === REVIEW
      ? reviewCards(source.data, state.due, world.module, random)
      : lessonCards(source.data, lessonId, world.module, random)),
    refresh: () => client.invalidateQueries({ queryKey: ['grow-summary', world.module] }),
  }
}
