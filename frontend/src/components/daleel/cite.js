/** How a passage is cited: its book (or source) and where in it. One wording for card, sheet and saved list. */
export const citeOf = (hit) => [hit.book || hit.source?.label, hit.locator].filter(Boolean).join(', ')

/** The saved passages, kept in the browser under whoever is logged in (lib/store/stored). */
export const SAVED_KEY = 'daleel-saved'
/** Where the saved list sits on the page, so the results can point to it. */
export const SAVED_ID = 'daleel-saved-list'

/** The first words of a passage, so a listed one can be judged before it is opened. */
const OPENING_CHARS = 70
export const openingOf = (hit) => {
  const text = hit.arabic || hit.english || ''
  return text.length > OPENING_CHARS ? `${text.slice(0, OPENING_CHARS)}…` : text
}
