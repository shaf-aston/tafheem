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
    // Leaving takes instant-ms: the box and its scrim fade (dialog[data-leaving],
    // styles/components.css) and only then does the dialog close. Esc is the
    // browser's close, which would be instant: its cancel is held back and sent
    // the same way. With the Animations setting off the wait is 0 and the
    // close is at once, as before.
    const leave = () => {
      if (!element.open || 'leaving' in element.dataset) return
      const root = getComputedStyle(document.documentElement)
      const ms = Number(root.getPropertyValue('--motion-instant-ms')) * Number(root.getPropertyValue('--motion-scale'))
      if (!(ms > 0)) return element.close()
      element.dataset.leaving = ''
      setTimeout(() => {
        delete element.dataset.leaving
        if (element.open) element.close()
      }, ms)
    }
    const cancel = (e) => { e.preventDefault(); leave() }
    element.addEventListener('cancel', cancel)
    if (open && !element.open) element.showModal()
    if (!open && element.open) leave()
    // Closed when its tab is hidden (App keeps the panel alive) and shown again
    // on return: a modal left open in a hidden tab would leave the page inert.
    return () => {
      element.removeEventListener('close', stale, true)
      element.removeEventListener('cancel', cancel)
      if (element.open) element.close()
    }
  }, [open])
  return ref
}

/** A click on the backdrop lands on the <dialog> itself, not its content: close then. */
export const closeOnBackdrop = (close) => (e) => { if (e.target === e.currentTarget) close(e) }
