/**
 * The one way to forget everything this app keeps in the browser: settings,
 * remembered choices (useRemembered), recent searches (useHistory), best streak,
 * the walked path (session.js).
 *
 * Clears the whole store rather than a written list of key names, which would
 * go stale the first time a panel remembers something new and then clear less
 * than the button says. The store holds this app's things only.
 *
 * Quiz answers are rows in a database on the machine, not in the browser, so
 * they go through lib/progress.js first; "clear it all" has to mean Mistakes
 * as well, or the button says more than it does.
 */
import { forgetProgress } from './progress'

/**
 * Forget it all, then reload.
 *
 * The reload is required, not tidiness: settings and remembered choices are
 * also held in React state, so clearing underneath them leaves stale values on
 * screen and the next click writes one straight back.
 */
export async function forgetSaved() {
  await forgetProgress()
  try {
    globalThis.localStorage?.clear()
  } catch {
    /* private browsing: nothing was kept */
  }
  globalThis.location?.reload()
}
