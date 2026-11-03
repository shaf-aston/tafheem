import { useEffect } from 'react'

import { motionOff } from './motion'

/**
 * Has an element watch the mouse: writes where the pointer is, relative to the
 * element's middle, as --look-x and --look-y (each -1 to 1, a quarter of the
 * screen away counting as all the way). The idle qalam leans and looks with
 * them (.qalam in motion.css). Mouse only: a finger is not somewhere to look
 * between taps. Nothing at all while Animations is off or reduce-motion is on,
 * and one write a frame however fast the mouse moves.
 */
export function useLook(ref, on = true) {
  useEffect(() => {
    const el = ref.current
    if (!on || !el || motionOff()) return undefined
    let frame = 0
    const move = (event) => {
      if (event.pointerType !== 'mouse' || frame) return
      frame = requestAnimationFrame(() => {
        frame = 0
        const box = el.getBoundingClientRect()
        const reach = Math.max(innerWidth, innerHeight) / 4
        const at = (from, to) => Math.max(-1, Math.min(1, (to - from) / reach)).toFixed(2)
        el.style.setProperty('--look-x', at(box.left + box.width / 2, event.clientX))
        el.style.setProperty('--look-y', at(box.top + box.height / 2, event.clientY))
      })
    }
    addEventListener('pointermove', move, { passive: true })
    return () => {
      removeEventListener('pointermove', move)
      cancelAnimationFrame(frame)
      el.style.removeProperty('--look-x')
      el.style.removeProperty('--look-y')
    }
  }, [ref, on])
}
