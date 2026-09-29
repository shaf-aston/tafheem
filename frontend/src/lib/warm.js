// Fetch ahead: `warm` when the page is idle, `onHover` for a likely click.
// prefetchQuery skips anything already cached, so callers need no guard.
const idle = globalThis.requestIdleCallback ?? ((fn) => setTimeout(fn, 200))

export const warm = (client, query) => idle(() => client.prefetchQuery(query))

export const onHover = (client, query) => {
  const go = () => client.prefetchQuery(query)
  return { onPointerEnter: go, onFocus: go }
}
