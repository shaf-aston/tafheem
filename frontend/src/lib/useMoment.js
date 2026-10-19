/**
 * A value that holds for a moment and then clears itself: a tool's "done"
 * look, or a destructive button armed for its second click. Setting it again
 * restarts the wait.
 */
import { useEffect, useState } from 'react'

/** How long a "Copied" look shows before the button reads as it did. */
export const COPY_RESET_MS = 2000

/** How long a destructive button stays armed before it goes quiet again. */
export const ARMED_MS = 5000

/** How long Start over waits, with an Undo showing, before it forgets anything. */
export const UNDO_MS = 5000

export function useMoment(ms, empty = null) {
  const [value, setValue] = useState(empty)
  useEffect(() => {
    if (value === empty) return undefined
    const timer = setTimeout(() => setValue(empty), ms)
    return () => clearTimeout(timer)
  }, [value, ms, empty])
  return [value, setValue]
}
