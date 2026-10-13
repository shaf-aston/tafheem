import { useRememberedFlag } from './useRemembered'

/**
 * Whether a hadith sets its English left and its Arabic right, as sunnah.com does: on until the
 * reader turns it off. One switch for every list of hadith cards and the book's reading options.
 */
export const useSideBySide = () => useRememberedFlag('hadith-side-by-side', true)
