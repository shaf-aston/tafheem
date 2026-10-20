import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { getSimilar, getSimilarSurah } from '../../api'
import { fetchSummary, recordAttempt } from '../../lib/progress'
import { pairId } from '../../lib/similar'
import copy from '../../similar.json'

/**
 * Every pair to learn in one surah: the pairs the catalogue records with one verse
 * here, the verse here asked first, in ayah order. Not every two verses of a group:
 * one group holds 218, and its pairs are the ones scholars actually set side by side.
 */
export function useSurahPairs(surah) {
  const query = useQuery({ queryKey: ['similar-surah', surah], queryFn: () => getSimilarSurah(surah) })
  const pairs = useMemo(() => {
    const here = (key) => key.startsWith(`${surah}:`)
    const seen = new Map()
    for (const group of query.data?.groups ?? []) {
      for (const [a, b] of group.pairs ?? []) {
        const [mine, twin] = here(a) ? [a, b] : [b, a]
        seen.set(pairId(a, b), { id: pairId(a, b), mine, twin })
      }
    }
    const ayah = (key) => Number(key.split(':')[1])
    return [...seen.values()].sort((x, y) => ayah(x.mine) - ayah(y.mine))
  }, [query.data, surah])
  return { query, pairs }
}

/** One pair, read from the asked verse's twins: its text, the twin's, and the paired changes. */
export function usePair(pair) {
  const [surah, ayah] = (pair?.mine ?? '0:0').split(':')
  const query = useQuery({
    queryKey: ['similar', surah, ayah],
    queryFn: () => getSimilar(surah, ayah),
    enabled: !!pair,
    staleTime: Infinity,
  })
  const partner = query.data?.partners.find((p) => p.key === pair?.twin) ?? null
  const mine = query.data && pair ? { key: pair.mine, text: query.data.text } : null
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
