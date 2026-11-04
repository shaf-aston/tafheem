/**
 * The first-visit plan for a component: read live from the shelf (so it follows the account, and a plan that landed
 * from another device shows at once), always through readPlan. `save` merges a patch into what is stored now, not what
 * was rendered, so two quick taps never undo each other.
 */
import { useCallback, useMemo } from 'react'

import { PLAN_KEY, readPlan, writePlan } from './plan'
import { readRaw, useStoredRaw, writeRaw } from '../store/stored'

export function usePlan() {
  const raw = useStoredRaw(PLAN_KEY)
  const plan = useMemo(() => readPlan(raw), [raw])
  const save = useCallback((patch) => writeRaw(PLAN_KEY, writePlan({ ...readPlan(readRaw(PLAN_KEY)), ...patch })), [])
  return { plan, save }
}
