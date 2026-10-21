import { PHONE, useMedia } from './useMedia'
import { useRememberedFlag } from './useRemembered'

/**
 * Whether hadith chains are hidden: one remembered switch, so a book, search and Starred agree.
 * Until a reader chooses, a phone hides them: four lines of حدثنا filled a card's first screen
 * there, and the words they carry waited behind "Show the rest". The chain stays a tap away.
 */
export function useHideChain() {
  const phone = useMedia(PHONE)
  return useRememberedFlag('hadith-hide-chain', phone)
}
