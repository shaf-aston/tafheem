// Fetch ahead: `warm` when the page is idle, `onHover` for a likely click.
// prefetchQuery skips anything already cached, so callers need no guard.
//
// `idle` has a deadline. Without one, requestIdleCallback waits for a frame
// with time to spare, and a page that is drawing (the backdrop) on a slower
// CPU never has one: measured on a phone profile, the fetch-ahead never ran
// and every tab was fetched only when tapped. Fast or slow, it now runs by
// IDLE_BY at the latest. Safari has no requestIdleCallback: a short timer.
export const IDLE_BY = 1500
export const idle = (fn) => (globalThis.requestIdleCallback
  ? globalThis.requestIdleCallback(fn, { timeout: IDLE_BY })
  : setTimeout(fn, 200))

// Runs `steps` one after another (each may return a promise), so a burst of
// fetch-ahead never fills the connection at once: a tab pressed meanwhile
// starts its own fetch straight away and shares the line with one step, not
// with all of them. A failed step does not stop the rest.
export async function inTurn(steps) {
  for (const step of steps) await Promise.resolve().then(step).catch(() => {})
}

export const warm = (client, query) => idle(() => client.prefetchQuery(query))

// A tab's `open` step for the common case: its opening data is one query.
export const load = (query) => (client) => client.prefetchQuery(query)

// One head start for every device: a mouse hovers, a finger presses down
// (~100ms before the click), a keyboard focuses. Phones have no hover, so
// hover alone left them with no head start at all.
export const ahead = (go) => ({ onPointerEnter: go, onPointerDown: go, onFocus: go })

export const onHover = (client, query) => ahead(() => client.prefetchQuery(query))
