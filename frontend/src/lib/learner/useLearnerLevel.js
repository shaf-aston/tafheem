/**
 * The learner's level for a component: what they chose (kept on their shelf, so it follows the account), and what
 * their answers make of it (lib/learner/learnerLevel.js). The answers are the progress overview, the same query Home reads;
 * a guest's are this device's own record, so their answers settle the level just the same.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getProfile } from './profile'
import { LEVEL_IDS, LEVEL_KEY, classify } from './learnerLevel'
import { overviewQuery } from './record'
import { useRemembered } from '../store/useRemembered'

export function useLearnerLevel() {
  const [name] = useState(getProfile)
  const [chosen, choose] = useRemembered(LEVEL_KEY, LEVEL_IDS, '')
  const overview = useQuery(overviewQuery(name))
  // `known`: the answers are in (or there are none to wait for), so the level will not move on its own until more come.
  return { ...classify(chosen, overview.data?.modules), chosen, choose, guest: !name, known: overview.isFetched }
}
