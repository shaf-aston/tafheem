/**
 * The Prayer world's record: the paths (from /api/grow/paths), the reader's
 * own record of each step (kept in this browser, lib/grow.js rules), the tiers
 * built from both, the step up next and the score. Shared by Grow's home, which
 * shows how far along it is, and the Prayer world, which practises it.
 */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { growPathsQuery } from '../api'
import config from '../grow.json'
import { score, tiersOf, upNext } from './grow'
import { progressKey } from './stored'
import { useRemembered } from './useRemembered'

export function usePrayerRecord() {
  const paths = useQuery(growPathsQuery)
  // The record is kept as JSON text in this browser only (useRemembered).
  const [saved, save] = useRemembered(progressKey(config['storage-key']))
  const record = useMemo(() => JSON.parse(saved || '{}'), [saved])
  const tiers = useMemo(() => tiersOf(config.tiers, paths.data), [paths.data])
  const next = useMemo(() => upNext(tiers, record), [tiers, record])
  return { paths, record, keep: (changed) => save(JSON.stringify(changed)), tiers, next, done: score(tiers, record) }
}
