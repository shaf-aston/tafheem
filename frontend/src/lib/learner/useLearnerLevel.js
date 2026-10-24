/**
 * The learner's level for a component: what they chose (kept on their shelf, so it follows the account), and what
 * their answers make of it (lib/learner/learnerLevel.js). The answers are the progress overview, the same query Home reads;
 * a guest has none (every guest shares one record), so a guest's level is always their own choice.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fetchOverview } from './progress'
import { getProfile } from './profile'
import { LEVEL_IDS, LEVEL_KEY, classify } from './learnerLevel'
import { useRemembered } from '../store/useRemembered'

export function useLearnerLevel() {
  const [name] = useState(getProfile)
  const [chosen, choose] = useRemembered(LEVEL_KEY, LEVEL_IDS, '')
  const overview = useQuery({ queryKey: ['overview', name], queryFn: fetchOverview, enabled: !!name, retry: false })
  return { ...classify(chosen, overview.data?.modules), chosen, choose, guest: !name }
}
