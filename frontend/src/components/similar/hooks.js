import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { similarAyahQuery, similarSurahQuery } from '../../api'
import { summaryQuery, useRecord } from '../../lib/learner/record'
import { pairsOf } from '../../lib/similar/similar'
import copy from '../../config/similar.json'

/** Every pair to learn in one surah (lib/similar/similar.js pairsOf). */
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
  const record = useRecord()
  const summary = useQuery({ ...summaryQuery(copy.module), retry: false })
  const byId = useMemo(() => new Map((summary.data ?? []).map((row) => [row.item, row])), [summary.data])
  const standing = (id) => (byId.get(id)?.due ? 'due' : byId.get(id)?.known ? 'known' : 'new')
  const file = async (id, correct) => {
    // A drill is over once filed, so its standing is re-read at once.
    await record.file({ module: copy.module, item: id, correct })
    record.refresh(copy.module)
  }
  return { standing, file }
}
