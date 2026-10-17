/**
 * A path world's paths, the browser-kept step record, its levels, next step and score.
 * Shared by Grow's home and the world's page (components/grow/PathWorld.jsx).
 */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { growPathsQuery } from '../api'
import config from '../grow.json'
import { levelsOf, score, tiersOf, upNext } from './grow'
import { progressKey } from './stored'
import { useRemembered } from './useRemembered'

export function usePathRecord(world) {
  const paths = useQuery(growPathsQuery)
  const [saved, save] = useRemembered(progressKey(config['storage-key']))
  const record = useMemo(() => JSON.parse(saved || '{}'), [saved])
  const tiers = useMemo(() => tiersOf(levelsOf(world), paths.data), [world, paths.data])
  const next = useMemo(() => upNext(tiers, record), [tiers, record])
  return { paths, record, keep: (changed) => save(JSON.stringify(changed)), tiers, next, done: score(tiers, record) }
}
