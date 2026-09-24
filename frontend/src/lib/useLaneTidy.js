import { useRememberedFlag } from './useRemembered'

/**
 * Whether Lane is shown without his authority lists and book pointers. One
 * remembered choice for every place Lane is quoted, on by default: the marks
 * serve a reader checking his sources, and hide the meaning from everyone else.
 */
export const useLaneTidy = () => useRememberedFlag('lane-tidy', true)

/** Lane's key, the same in the dictionary shelf and in Daleel's sources. */
export const LANE = 'lane'

/** The words on the switch, the same wherever it appears. */
export const LANE_TIDY_LABEL = 'Clean view'
export const LANE_TIDY_TITLE = 'Hide the source abbreviations (S, Msb, K) and the printed-book pointers (q. v., ↓)'
