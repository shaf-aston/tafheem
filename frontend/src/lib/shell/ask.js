/**
 * "Put the cursor in the command line": the pen in the header asks for it, the
 * header's bar answers (components/shell/CommandBar.jsx). An event rather than a
 * ref, so the shell need not reach into the bar to move its focus.
 */
const ASK = 'tafheem:ask'

export const ask = () => globalThis.dispatchEvent(new Event(ASK))

/** Listen for `ask`; returns the way to stop. */
export function onAsk(handler) {
  globalThis.addEventListener(ASK, handler)
  return () => globalThis.removeEventListener(ASK, handler)
}
