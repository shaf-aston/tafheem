// Fetch ahead: `warm` when the page is idle, `onHover` for a likely click.
// prefetchQuery skips anything already cached, so callers need no guard.
export const idle = globalThis.requestIdleCallback ?? ((fn) => setTimeout(fn, 200))

export const warm = (client, query) => idle(() => client.prefetchQuery(query))

// A tab's `open` step for the common case: its opening data is one query.
export const load = (query) => (client) => client.prefetchQuery(query)

// One head start for every device: a mouse hovers, a finger presses down
// (~100ms before the click), a keyboard focuses. Phones have no hover, so
// hover alone left them with no head start at all.
export const ahead = (go) => ({ onPointerEnter: go, onPointerDown: go, onFocus: go })

export const onHover = (client, query) => ahead(() => client.prefetchQuery(query))
