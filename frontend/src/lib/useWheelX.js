/**
 * A sideways strip that a mouse wheel turns sideways. Most wheels only roll up
 * and down, and a strip that ignores them can only be moved by its scrollbar,
 * which .strip-x hides. Non-passive, so the page does not scroll underneath.
 * Returns the ref for the strip.
 */
import { useEffect, useRef } from 'react'

export function useWheelX() {
  const ref = useRef(null)
  useEffect(() => {
    const strip = ref.current
    if (!strip) return undefined
    const turn = (e) => {
      if (Math.abs(e.deltaY) <= Math.abs(e.deltaX) || strip.scrollWidth <= strip.clientWidth) return
      e.preventDefault()
      strip.scrollLeft += e.deltaY
    }
    strip.addEventListener('wheel', turn, { passive: false })
    return () => strip.removeEventListener('wheel', turn)
  }, [])
  return ref
}
