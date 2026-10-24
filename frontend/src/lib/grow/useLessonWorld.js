/**
 * Any lessons world's data: its items (`load` → { order, all }), the learner's record for `module`
 * (server summary: seen, due, known), the next lesson's picks, the stage, `items` (each with its status, for a scene), and the cards on demand.
 * Configs: lib/grow/useBasicsWorld.js, lib/useWordsWorld.js, lib/useHadithWorld.js, lib/useQuranWorld.js; numbers from worlds.json.
 */
import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { itemsOf, lessonItems, stageOf } from './lesson'
import { fetchSummary } from '../learner/progress'

export function useLessonWorld({ world, module, load, keyOf, cards, alsoRefresh = [] }) {
  const client = useQueryClient()
  const source = useQuery({ queryKey: ['grow-source', world.id], queryFn: load, staleTime: Infinity })
  const summary = useQuery({ queryKey: ['grow-summary', module], queryFn: () => fetchSummary(module) })
  const { lesson, stages } = world

  const state = useMemo(() => {
    if (!source.data || !summary.data) return null
    const { order } = source.data
    const inSet = new Set(order.map(keyOf))
    const rows = summary.data
    const seen = new Set(rows.map((row) => row.item))
    const due = rows.filter((row) => row.due).sort((a, b) => a.dueAt.localeCompare(b.dueAt)).map((row) => row.item)
    const learnt = rows.filter((row) => row.known && inSet.has(row.item)).length
    const next = lessonItems({ ...source.data, seen, due, keyOf, fresh: lesson.new, most: lesson['most-new'], size: lesson.size })
    return { items: itemsOf(order, keyOf, rows), learnt, next, fresh: order.filter((item) => !seen.has(keyOf(item))).length, dueCount: due.length, stage: stageOf(learnt, stages) }
  }, [source.data, summary.data, keyOf, lesson, stages])

  return {
    world,
    stages,
    ready: Boolean(state),
    // The record is being re-read (after a lesson): a lesson dealt now would offer the items just answered as new.
    settling: summary.isFetching,
    error: source.error ?? summary.error,
    retry: () => { source.refetch(); summary.refetch() },
    ...(state ?? { dueCount: 0, items: [] }),
    makeLesson: (random = Math.random) => cards(state.next, source.data.all, random),
    // After a lesson: re-read this record and any view that shares it.
    refresh: () => {
      client.invalidateQueries({ queryKey: ['grow-summary', module] })
      for (const key of alsoRefresh) client.invalidateQueries({ queryKey: [key] })
    },
  }
}
