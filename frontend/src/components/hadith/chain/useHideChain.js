import { PHONE } from '../../../lib/hooks/useMedia'
import { useRememberedFlag } from '../../../lib/store/useRemembered'

// Read once as the app opens: turning a phone sideways must not flip every card's chain back on.
const PHONE_AT_START = typeof matchMedia === 'function' && matchMedia(PHONE).matches

/**
 * Whether hadith chains are hidden: one remembered switch, so a book, search and Starred agree.
 * Until a reader chooses, a phone hides them: four lines of حدثنا filled a card's first screen
 * there, and the words they carry waited behind "Show the rest". The chain stays a tap away.
 */
export function useHideChain() {
  return useRememberedFlag('hadith-hide-chain', PHONE_AT_START)
}
