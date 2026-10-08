import { useEffect, useState } from 'react'

// How far through a sticky track the reader is: 0 at its top, 1 once its
// bottom reaches the viewport's.
export const trackProgress = (r) => {
  const travel = r.height - innerHeight
  return travel > 0 ? -r.top / travel : 0
}

const RISE_SHARE = 0.85 // share of an element's height that has to scroll past before it counts as risen

// How far an element has risen into view, eased out.
export const riseProgress = (r) => {
  const p = Math.min(1, Math.max(0, (innerHeight - r.top) / (Math.min(r.height, innerHeight) * RISE_SHARE)))
  return 1 - (1 - p) ** 3
}

// 0 as an element's top enters at the bottom, 1 once its middle reaches the screen's middle, eased out.
export const settleProgress = (r) => {
  const p = Math.min(1, Math.max(0, (innerHeight - r.top) / ((innerHeight + r.height) / 2)))
  return 1 - (1 - p) ** 3
}

// 0 to 1, both directions, measured once per frame while the element is on
// screen (one more measure as it leaves, so the end values are exact).
export default function useScrollProgress(ref, measure = trackProgress) {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const node = ref.current
    let raf = 0
    function frame() {
      raf = 0
      setProgress(Math.min(1, Math.max(0, measure(node.getBoundingClientRect()))))
    }
    function queue() { if (!raf) raf = requestAnimationFrame(frame) }
    function listen(on) {
      const toggle = on ? addEventListener : removeEventListener
      toggle('scroll', queue, { passive: true })
      toggle('resize', queue)
    }
    const watcher = new IntersectionObserver(([e]) => { listen(e.isIntersecting); queue() })
    watcher.observe(node)
    frame()
    return () => {
      watcher.disconnect()
      listen(false)
      cancelAnimationFrame(raf)
    }
  }, [ref, measure])

  return progress
}
