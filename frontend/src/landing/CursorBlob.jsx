import { useEffect, useRef, useState } from 'react'

// A gold circle that trails the real pointer with mix-blend-mode: difference,
// inverting whatever it crosses, and grows over links/buttons. Ported from
// v2's #cursor-dot. Skips entirely on touch devices and under
// prefers-reduced-motion: the native cursor is always what actually clicks.
export default function CursorBlob() {
  const dotRef = useRef(null)
  const [enabled] = useState(
    () => matchMedia('(hover: hover)').matches
      && matchMedia('(pointer: fine)').matches
      && !matchMedia('(prefers-reduced-motion: reduce)').matches,
  )

  useEffect(() => {
    if (!enabled) return
    const dot = dotRef.current
    let x = window.innerWidth / 2
    let y = window.innerHeight / 2
    let tx = x
    let ty = y
    let raf

    // Hidden until the mouse first moves, and while it is outside the window,
    // so the blob never sits parked mid-screen on its own.
    function onMove(e) {
      if (!dot.classList.contains('on')) { x = e.clientX; y = e.clientY; dot.classList.add('on') }
      tx = e.clientX; ty = e.clientY
    }
    function onLeave() { dot.classList.remove('on') }
    function onOver(e) { if (e.target.closest('a, button, .strip-item')) dot.classList.add('grow') }
    function onOut(e) { if (e.target.closest('a, button, .strip-item')) dot.classList.remove('grow') }

    function tick() {
      x += (tx - x) * 0.18
      y += (ty - y) * 0.18
      dot.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`
      raf = requestAnimationFrame(tick)
    }

    window.addEventListener('mousemove', onMove)
    document.addEventListener('mouseover', onOver)
    document.addEventListener('mouseout', onOut)
    document.documentElement.addEventListener('mouseleave', onLeave)
    raf = requestAnimationFrame(tick)

    return () => {
      window.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseover', onOver)
      document.removeEventListener('mouseout', onOut)
      document.documentElement.removeEventListener('mouseleave', onLeave)
      cancelAnimationFrame(raf)
    }
  }, [enabled])

  if (!enabled) return null
  return <div ref={dotRef} className="cursor-blob" aria-hidden="true" />
}
