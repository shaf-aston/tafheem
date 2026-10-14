/**
 * The logged-in learner's XP and level, kept current by every saved answer
 * (lib/rewards.js announce), and the last earning while it is still floating.
 * One read when the page opens; after that each answer's own reply updates it,
 * so no tab asks the server twice.
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
