/**
 * The cursor light: one faint circle that follows the pointer on every tab, in
 * that tab's colour (--c, set by App).
 *
 * Mounted once by App, never by a panel, so no page wires anything and a page
 * added later has it for free. Its look and strength live in theme.json and
 * index.css (.cursor-light); the Animations setting turns it off.
 *
 * Moved by transform alone, one write per animation frame, so following the
 * pointer never repaints the page under it.
 */
import { useEffect, useRef } from 'react'

export default function CursorLight() {
  const light = useRef(null)

  useEffect(() => {
    const node = light.current
    if (!node) return

    let x = 0
    let y = 0
    let queued = false

    const draw = () => {
      queued = false
      node.style.transform = `translate3d(${x}px, ${y}px, 0)`
    }
    const show = (on) => { if (node.dataset.on !== on) node.dataset.on = on }

    const move = (event) => {
      x = event.clientX
      y = event.clientY
      show('1')
      if (queued) return
      queued = true
      requestAnimationFrame(draw)
    }
    // A tap or a touch scroll must not leave the light where the finger was.
    const off = () => show('0')

    document.addEventListener('pointermove', move, { passive: true })
    document.documentElement.addEventListener('pointerleave', off)
    document.addEventListener('pointercancel', off)
    window.addEventListener('blur', off)
    return () => {
      document.removeEventListener('pointermove', move)
      document.documentElement.removeEventListener('pointerleave', off)
      document.removeEventListener('pointercancel', off)
      window.removeEventListener('blur', off)
    }
  }, [])

  return <div ref={light} className="cursor-light" data-on="0" aria-hidden="true" />
}
