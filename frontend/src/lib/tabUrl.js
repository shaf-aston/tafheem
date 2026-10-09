/**
 * The one place that knows how a place in the app is written into the address.
 *
 * The address bar shows only the tab: /app/nahw. What the tab was opened with
 * (a word, an ayah address) and the choices inside it (which view, topic,
 * question) ride on the history entry instead, out of sight. The browser keeps
 * that across a reload and gives each back-arrow step its own, so back still
 * walks searches inside a tab. See lib/journey.js, the only caller that writes.
 *
 * A link carries the same things as a query, /app/nahw?q=...&view=..., and so
 * does the old form, /app?tab=nahw&q=... Both are read once on arrival, then
 * the address is tidied. `shareLink` writes that form back out.
 */

// I'raab and tarkeeb were two tabs before they became two views of one.
// Links people already have keep working rather than landing nowhere.
const LEGACY = { iraab: 'nahw', tarkeeb: 'nahw' }

const APP = '/app'
const TAB_IN_PATH = /^\/app\/([^/]+)\/?$/
const VALUE = 'q'

/** Where a tab lives: /app/nahw. */
export const tabAddress = (tab) => `${APP}/${tab}`

/**
 * The place as the current entry holds it: `{tab, value, view}`, tab as written
 * (not yet checked against the tabs). An entry this app wrote carries value and
 * view in its state; anything else is a link, read from its query.
 */
function current() {
  const url = new URL(window.location.href)
  const query = Object.fromEntries(url.searchParams)
  const tab = url.pathname.match(TAB_IN_PATH)?.[1] ?? query.tab ?? null
  const state = window.history.state
  if (state && typeof state.view === 'object' && state.view) return { tab, value: state.value ?? null, view: state.view }
  const view = { ...query }
  delete view.tab
  delete view[VALUE]
  return { tab, value: query[VALUE] || null, view }
}

/**
 * Tab plus what it was opened with. A bare address names no tab, and says so
 * with null rather than the first tab: the journey opens it where the reader
 * last was, which the first tab is not.
 */
export function readRouteFromUrl(tabs) {
  try {
    const { tab, value } = current()
    if (!tab) return { tab: null, value }
    return { tab: LEGACY[tab] ?? tabs.find((one) => one.id === tab)?.id ?? tabs[0].id, value }
  } catch {
    return { tab: null, value: null }
  }
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
    const now = current()
    // Choices inside a tab (which view, topic, question) belong to that tab only.
    const view = now.tab === id ? now.view : {}
    window.history[replace ? 'replaceState' : 'pushState']({ ...state, value, view }, '', tabAddress(id))
  } catch {
    /* URL sync is a convenience; the tab still switches without it */
  }
}

/** One in-tab choice from the current entry, or null when absent or not allowed. */
export function readViewParam(key, allowed = null) {
  try {
    const value = current().view[key]
    return value && (!allowed || allowed.includes(value)) ? value : null
  } catch {
    return null
  }
}

/** Write in-tab choices onto the current entry without a new back-arrow step; '' or null removes one. */
export function writeViewParams(values) {
  try {
    const now = current()
    const view = { ...now.view }
    for (const [key, value] of Object.entries(values)) {
      if (value) view[key] = value
      else delete view[key]
    }
    const path = now.tab ? tabAddress(now.tab) : window.location.pathname
    window.history.replaceState({ ...window.history.state, value: now.value, view }, '', path)
  } catch {
    /* a convenience; the choice still holds on screen */
  }
}

/** A link to exactly this place: the tab in the path, the rest as a query. */
export function shareLink() {
  const { tab, value, view } = current()
  const url = new URL(tab ? tabAddress(tab) : APP, window.location.origin)
  if (value) url.searchParams.set(VALUE, value)
  for (const [key, one] of Object.entries(view)) url.searchParams.set(key, one)
  return url.href
}
