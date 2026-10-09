/**
 * A native <dialog> kept in step with an `open` prop: showModal on true, close
 * on false. Native, so Esc, the backdrop and the focus trap come free. Returns
 * the ref for the <dialog>. Was copied into four panels.
 */
import { useEffect, useRef } from 'react'

export function useModal(open) {
  const ref = useRef(null)
  useEffect(() => {
    const element = ref.current
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
    // Closed when its tab is hidden (App keeps the panel alive) and shown again
    // on return: a modal left open in a hidden tab would leave the page inert.
    return () => { if (element.open) element.close() }
  }, [open])
  return ref
}
