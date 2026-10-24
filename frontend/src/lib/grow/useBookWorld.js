/**
 * The book worlds' data (Fiqh, Aqidah, Nahw, Sarf), each: the book's index (lib/grow/bookSplit.js), the learner's record for its `module`,
 * each lesson's status, the next lesson and what is due, and a lesson's cards. A part's cards are fetched only when the
 * screen needs them: its lessons are open, one of its lessons is being played, or a review draws on it. `view` is
 * GrowPanel's (its address); `dealable` says the cards for it are in. The book is static: when the learner's record cannot
 * be read (the server is down), the lessons still show and play, as if nothing were answered yet (`offline`). Rules: lib/grow/bookLesson.js; entry: worlds.json.
 */
import { useQueries } from '@tanstack/react-query'

import { lessonCards, partOfLesson, partsDue, partsOf, reviewCards } from './bookLesson'
import { indexPath, partPath } from './bookSplit'
import { summaryQuery, useRecord } from '../learner/record'

/** Where the book world last studied is remembered (GrowPanel writes it, Grow home leads with it). */
export const LAST_BOOK = 'grow-last-book'

/** The lesson id a review goes by, in the address and to `makeLesson`. */
export const REVIEW = 'review'

async function load(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Could not load the book (${response.status})`)
  return response.json()
}

// The record when it cannot be read: nothing answered.
const NOTHING = []

/** The parts `view` needs the cards of, in this world. */
function partsWanted(world, view, index, due) {
  if (!index || view?.id !== world.id) return []
  if (view.at === 'lesson') return view.lesson === REVIEW ? partsDue(index, due) : [partOfLesson(index, view.lesson)].filter(Boolean)
  return view.part && index.parts.some((part) => part.id === view.part) ? [view.part] : []
}

// Each book's statuses, kept per index and record so a render does not re-derive them.
const derived = new WeakMap()
function stateOf(index, record) {
  if (!index || !record) return null
  const seen = derived.get(index)
  if (seen?.record === record) return seen.state
  const state = partsOf(index, record)
  derived.set(index, { record, state })
  return state
}

/** Every book world's data, by id: one entry per world in `worlds` (worlds.json's entries of kind `book`). */
export function useBookWorlds(worlds, view) {
  const { refresh } = useRecord()
  const sources = useQueries({
    queries: worlds.map((world) => ({ queryKey: ['grow-source', world.id], queryFn: () => load(indexPath(world.source)), staleTime: Infinity })),
  })
  const summaries = useQueries({
    queries: worlds.map((world) => ({ ...summaryQuery(world.module), retry: 1 })),
  })
  const records = summaries.map((summary) => summary.data ?? (summary.isError ? NOTHING : null))
  const states = worlds.map((_, i) => stateOf(sources[i].data, records[i]))
  const wanted = worlds.flatMap((world, i) => partsWanted(world, view, sources[i].data, states[i]?.due ?? []).map((id) => ({ world, id })))
  const parts = useQueries({
    queries: wanted.map(({ world, id }) => ({ queryKey: ['grow-part', world.id, id], queryFn: () => load(partPath(world.source, id)), staleTime: Infinity })),
  })

  return Object.fromEntries(worlds.map((world, i) => {
    const source = sources[i]
    const summary = summaries[i]
    const state = states[i]
    const mine = parts.filter((_, at) => wanted[at].world === world)
    const withCards = { parts: mine.map((part) => part.data).filter(Boolean) }
    // As a lessons world's (lib/grow/useLessonWorld.js): a review dealt from a record behind its answers would miss them.
    const behind = summary.isSuccess && summary.isStale && !summary.isFetching
    return [world.id, {
      world,
      ready: Boolean(state),
      behind,
      dealable: Boolean(state) && mine.every((part) => part.data) && !behind && !summary.isFetching,
      error: source.error ?? mine.find((part) => part.error)?.error,
      offline: summary.isError,
      retry: () => { source.refetch(); summary.refetch(); for (const part of mine) part.refetch() },
      book: source.data,
      ...(state ?? { parts: [], areas: [], next: null, due: [] }),
      // A lesson's cards, or the due ones for REVIEW, from the parts loaded for `view`; null when there is no such lesson
      // or the book is not in yet.
      makeLesson: (lessonId, random = Math.random) => (!state ? null : lessonId === REVIEW
        ? reviewCards(withCards, state.due, world, random)
        : lessonCards(withCards, lessonId, world, random)),
      refresh: () => refresh(world.module),
    }]
  }))
}
