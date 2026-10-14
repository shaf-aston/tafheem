/**
 * The Prayer world's paths, the browser-kept step record, tiers, next step and score.
 * Shared by Grow's home and the Prayer world.
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
  const [saved, save] = useRemembered(progressKey(config['storage-key']))
  const record = useMemo(() => JSON.parse(saved || '{}'), [saved])
  const tiers = useMemo(() => tiersOf(config.tiers, paths.data), [paths.data])
  const next = useMemo(() => upNext(tiers, record), [tiers, record])
  return { paths, record, keep: (changed) => save(JSON.stringify(changed)), tiers, next, done: score(tiers, record) }
}
