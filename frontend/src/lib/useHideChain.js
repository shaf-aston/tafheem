import { useRememberedFlag } from './useRemembered'

/** Whether hadith chains are hidden: one remembered switch, so a book, search and Starred agree. */
export const useHideChain = () => useRememberedFlag('hadith-hide-chain', false)
