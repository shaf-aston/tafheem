/**
 * A book world's data (Fiqh, Nahw, Sarf): the book's index (lib/bookSplit.js), the learner's record for its `module`,
 * each lesson's status, the next lesson and what is due, and a lesson's cards. A part's cards are fetched only when the
 * screen needs them: its lessons are open, one of its lessons is being played, or a review draws on it. `view` is
 * GrowPanel's (its address); `dealable` says the cards for it are in. Rules: lib/bookLesson.js; entry: worlds.json.
 */
import { useMemo } from 'react'
import { useQueries, useQuery, useQueryClient } from '@tanstack/react-query'

import { lessonCards, partOfLesson, partsDue, partsOf, reviewCards } from './bookLesson'
import { indexPath, partPath } from './bookSplit'
import { fetchSummary } from './progress'

/** The lesson id a review goes by, in the address and to `makeLesson`. */
export const REVIEW = 'review'

async function load(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Could not load the book (${response.status})`)
  return response.json()
}

/** The parts `view` needs the cards of, in this world. */
function partsWanted(world, view, index, due) {
  if (!index || view?.id !== world.id) return []
  if (view.at === 'lesson') return view.lesson === REVIEW ? partsDue(index, due) : [partOfLesson(index, view.lesson)].filter(Boolean)
  return view.part && index.parts.some((part) => part.id === view.part) ? [view.part] : []
}

export function useBookWorld(world, view) {
  const client = useQueryClient()
  const source = useQuery({ queryKey: ['grow-source', world.id], queryFn: () => load(indexPath(world.source)), staleTime: Infinity })
  const summary = useQuery({ queryKey: ['grow-summary', world.module], queryFn: () => fetchSummary(world.module) })
  const state = useMemo(() => (source.data && summary.data ? partsOf(source.data, summary.data) : null), [source.data, summary.data])

  const wanted = partsWanted(world, view, source.data, state?.due ?? [])
  const parts = useQueries({
    queries: wanted.map((id) => ({ queryKey: ['grow-part', world.id, id], queryFn: () => load(partPath(world.source, id)), staleTime: Infinity })),
  })
  const loaded = parts.every((part) => part.data)
  const withCards = { parts: parts.map((part) => part.data).filter(Boolean) }

  return {
    world,
    ready: Boolean(state),
    dealable: Boolean(state) && loaded,
    error: source.error ?? summary.error ?? parts.find((part) => part.error)?.error,
    retry: () => { source.refetch(); summary.refetch(); for (const part of parts) part.refetch() },
    book: source.data,
    ...(state ?? { parts: [], areas: [], next: null, due: [] }),
    // A lesson's cards, or the due ones for REVIEW, from the parts loaded for `view`; null when there is no such lesson.
    makeLesson: (lessonId, random = Math.random) => (lessonId === REVIEW
      ? reviewCards(withCards, state.due, world.module, random)
      : lessonCards(withCards, lessonId, world.module, random)),
    refresh: () => client.invalidateQueries({ queryKey: ['grow-summary', world.module] }),
  }
}
