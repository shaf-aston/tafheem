/**
 * The learner's XP and level: read once, then kept current by each answer's reply.
 * `gain` is the last earning while its "+10" floats.
 */
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchRewards } from './progress'
import { FLOAT_MS, onEarned } from './rewards'

export function useRewards(name) {
  const client = useQueryClient()
  const rewards = useQuery({ queryKey: ['rewards', name], queryFn: fetchRewards, enabled: !!name, retry: false })
  const [gain, setGain] = useState(null)

  useEffect(() => onEarned((saved) => {
    client.setQueryData(['rewards', name], saved.rewards)
    if (saved.earned > 0) setGain({ n: saved.earned, at: Date.now() })
  }), [client, name])

  useEffect(() => {
    if (!gain) return undefined
    const wait = setTimeout(() => setGain(null), FLOAT_MS)
    return () => clearTimeout(wait)
  }, [gain])

  return { rewards: rewards.data, gain }
}
