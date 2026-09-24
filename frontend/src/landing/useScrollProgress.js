import { useEffect, useState } from 'react'

// 0 to 1: how far the reader has scrolled through a tall track that holds a
// sticky child. Both directions, throttled to one measure per frame.
export default function useScrollProgress(trackRef) {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let raf = 0
    function measure() {
      raf = 0
      const r = trackRef.current.getBoundingClientRect()
      const travel = r.height - window.innerHeight
      setProgress(travel > 0 ? Math.min(1, Math.max(0, -r.top / travel)) : 0)
    }
    function onScroll() { if (!raf) raf = requestAnimationFrame(measure) }
    measure()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      cancelAnimationFrame(raf)
    }
  }, [trackRef])

  return progress
}
