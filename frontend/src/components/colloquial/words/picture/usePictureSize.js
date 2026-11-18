// The picture's size on screen, in pixels: what a label in its rail needs to turn its own measured
// height into the drawing's units. Null until laid out (and in a test, where nothing is).
import { useLayoutEffect, useState } from 'react'

export default function usePictureSize(svg) {
  const [size, setSize] = useState(null)
  useLayoutEffect(() => {
    const el = svg.current
    if (!el) return undefined
    const read = () => {
      const { width, height } = el.getBoundingClientRect?.() ?? {}
      setSize(width && height ? { w: width, h: height } : null)
    }
    read()
    if (typeof ResizeObserver === 'undefined') return undefined
    const watch = new ResizeObserver(read)
    watch.observe(el)
    return () => watch.disconnect()
  }, [svg])
  return size
}
