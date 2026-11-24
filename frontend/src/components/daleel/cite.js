/** How a passage is cited: its book (or source) and where in it. One wording for card, sheet and saved list. */
export const citeOf = (hit) => [hit.book || hit.source?.label, hit.locator].filter(Boolean).join(', ')

/** The saved passages, kept in the browser under whoever is logged in (lib/store/stored). */
export const SAVED_KEY = 'daleel-saved'
