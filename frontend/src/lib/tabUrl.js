/**
 * The one place that knows how a place in the app is written into the address.
 *
 * Two things go in: which tab, and what it was opened with (a word, an ayah
 * address, a question). The second is what makes the browser's back arrow mean
 * something inside a tab: without it, ten dictionary searches share one address
 * and back leaves the app. See lib/journey.js, the only caller that writes.
 */

// I'raab and tarkeeb were two tabs before they became two views of one.
// Links people already have keep working rather than landing nowhere.
const LEGACY = { iraab: 'nahw', tarkeeb: 'nahw' }

const VALUE = 'q'

/** The tab id the current URL asks for, or the first tab. */
export function readTabFromUrl(tabs) {
  try {
    const requested = new URLSearchParams(window.location.search).get('tab')
    return LEGACY[requested]
      ?? tabs.find((tab) => tab.id === requested)?.id
      ?? tabs[0].id
  } catch {
    return tabs[0].id
  }
}

/**
 * Tab plus what it was opened with, as the address currently has it. A bare
 * address names no tab, and says so with null rather than the first tab: the
 * journey opens it where the reader last was, which the first tab is not.
 */
export function readRouteFromUrl(tabs) {
  let value = null
  let named = false
  try {
    const params = new URLSearchParams(window.location.search)
    value = params.get(VALUE) || null
    named = params.has('tab')
  } catch {
    /* no URL to read, the tab alone is enough */
  }
  return { tab: named ? readTabFromUrl(tabs) : null, value }
}

/** What `writeTabToUrl` stamped on the current history entry, if anything. */
export function readStateFromHistory() {
  try {
    return window.history.state ?? {}
  } catch {
    return {}
  }
}

/**
 * Put a place into the address bar without reloading.
 *
 * `state` rides along on the history entry: journey.js stores the step number
 * there, which is what lets a back press say which step it landed on rather
 * than only that something moved.
 */
export function writeTabToUrl(id, value = null, { replace = false, state = {} } = {}) {
  try {
    const url = new URL(window.location.href)
    // Choices inside a tab (which view, topic, question) belong to that tab only.
    if (url.searchParams.get('tab') !== id) for (const key of VIEW_KEYS) url.searchParams.delete(key)
    url.searchParams.set('tab', id)
    if (value) url.searchParams.set(VALUE, value)
    else url.searchParams.delete(VALUE)
    window.history[replace ? 'replaceState' : 'pushState'](state, '', url)
  } catch {
    /* URL sync is a convenience; the tab still switches without it */
  }
}

// Choices inside a tab written into the address, so a link or reload lands on them.
const VIEW_KEYS = ['view', 'mode', 'topic', 'kind', 'show', 'question']

/** One in-tab choice from the address, or null when absent or not allowed. */
export function readViewParam(key, allowed = null) {
  try {
    const value = new URLSearchParams(window.location.search).get(key)
    return value && (!allowed || allowed.includes(value)) ? value : null
  } catch {
    return null
  }
}

/** Write in-tab choices into the address without a new back-arrow step; '' or null removes one. */
export function writeViewParams(values) {
  try {
    const url = new URL(window.location.href)
    for (const [key, value] of Object.entries(values)) {
      if (value) url.searchParams.set(key, value)
      else url.searchParams.delete(key)
    }
    window.history.replaceState(window.history.state, '', url)
  } catch {
    /* a convenience; the choice still holds on screen */
  }
}
