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
    // A close event that arrives once the dialog is open again (React's dev
    // double run closes and reshows it at once) is stopped before onClose.
    const stale = (e) => element.open && e.stopImmediatePropagation()
    element.addEventListener('close', stale, true)
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
    // Closed when its tab is hidden (App keeps the panel alive) and shown again
    // on return: a modal left open in a hidden tab would leave the page inert.
    return () => {
      element.removeEventListener('close', stale, true)
      if (element.open) element.close()
    }
  }, [open])
  return ref
}
