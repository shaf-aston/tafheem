import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { similarAyahQuery, similarSurahQuery } from '../../api'
import { fetchSummary, recordAttempt } from '../../lib/progress'
import { pairsOf } from '../../lib/similar'
import copy from '../../config/similar.json'

/** Every pair to learn in one surah (lib/similar.js pairsOf). */
export function useSurahPairs(surah) {
  const query = useQuery(similarSurahQuery(surah))
  const pairs = useMemo(() => pairsOf(query.data, surah), [query.data, surah])
  return { query, pairs }
}

/** One pair, read from the asked verse's twins: its text, the twin's, and the paired changes. */
export function usePair(pair) {
  const query = useQuery({ ...similarAyahQuery(pair?.mine ?? '0:0'), enabled: !!pair })
  const partner = query.data?.partners.find((p) => p.key === pair?.twin) ?? null
  const mine = query.data && pair ? { key: pair.mine, text: query.data.text, after: query.data.after ?? '' } : null
  return { query, mine, partner }
}

/** Each pair's standing in the progress store, and the way to file a finished drill. */
export function useMastery() {
  const client = useQueryClient()
  const key = ['progress', copy.module]
  const summary = useQuery({ queryKey: key, queryFn: () => fetchSummary(copy.module), retry: false })
  const byId = useMemo(() => new Map((summary.data ?? []).map((row) => [row.item, row])), [summary.data])
  const standing = (id) => (byId.get(id)?.due ? 'due' : byId.get(id)?.known ? 'known' : 'new')
  const file = async (id, correct) => {
    await recordAttempt({ module: copy.module, item: id, correct })
    client.invalidateQueries({ queryKey: key })
  }
  return { standing, file }
}
