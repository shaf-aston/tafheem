/**
 * True once an element has entered (or come near) the viewport, then stays true.
 *
 * One hook for two jobs: reveal-on-enter (threshold, no margin) and lazy
 * loading ahead of the scroll (margin like '600px'). Replaces the landing's
 * useRevealOnScroll and lib/useNearViewport, which did the same thing twice.
 * once: false tracks leaving too, for work that should stop offscreen.
 */
import { useEffect, useRef, useState } from 'react'

export function useInView({ margin = '0px', threshold = 0, once = true } = {}) {
  const ref = useRef(null)
  // Without IntersectionObserver (tests, older browsers) everything counts as
  // in view: shown is better than blank.
  const [inView, setInView] = useState(() => !globalThis.IntersectionObserver)

  const done = once && inView
  useEffect(() => {
    const node = ref.current
    if (done || !node) return
    const observer = new IntersectionObserver(
      ([entry]) => (once ? entry.isIntersecting && setInView(true) : setInView(entry.isIntersecting)),
      { rootMargin: margin, threshold },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [done, once, margin, threshold])

  return [ref, inView]
}
