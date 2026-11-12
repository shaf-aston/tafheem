/**
 * Home's hint for the number keys: a faded keycap under the strip, its arrow
 * pointing up at a tab, hopping 1 → 2 → … along every tab on show. The motion
 * says "press this number for this tab" with no words. It makes one pass each
 * time Home opens, then rests out of sight: looping for ever, it was the only
 * motion in the app that never stopped. Hovering the strip brings it back, clear,
 * hopping again. Look in styles/components.css (.key-hint).
 */
import { useEffect, useRef, useState } from 'react'

import { motionOff } from '../../lib/motion/motion'
import { motion } from '../../theme'

// `strip` is the tablist.
export default function KeyHint({ strip }) {
  const [spot, setSpot] = useState(null)
  const [resting, setResting] = useState(false)
  const at = useRef(0)

  useEffect(() => {
    // Its number is the tab's place in the strip (the key that opens it), so a
    // tab a narrow screen hides is skipped, never renumbered.
    const hop = () => {
      const tabs = [...(strip.current?.children ?? [])]
      if (!tabs.some((tab) => tab.offsetWidth > 0)) return false
      let n = at.current % tabs.length
      while (tabs[n].offsetWidth === 0) n = (n + 1) % tabs.length
      const tab = tabs[n]
      setSpot({ n: n + 1, x: tab.offsetLeft + tab.offsetWidth / 2 })
      at.current = n + 1
      return at.current >= tabs.length
    }
    hop()
    if (motionOff()) return undefined
    let timer = null
    let hovered = false
    const run = () => {
      clearInterval(timer)
      timer = setInterval(() => {
        // The first pass ends at the last tab; after it, it hops only while the strip is under the pointer.
        if (hop() && !hovered) { clearInterval(timer); setResting(true) }
      }, motion['key-hint-ms'])
    }
    const host = strip.current?.parentElement
    const enter = () => { hovered = true; at.current = 0; setResting(false); hop(); run() }
    const leave = () => { hovered = false }
    host?.addEventListener('pointerenter', enter)
    host?.addEventListener('pointerleave', leave)
    run()
    return () => {
      clearInterval(timer)
      host?.removeEventListener('pointerenter', enter)
      host?.removeEventListener('pointerleave', leave)
    }
  }, [strip])

  if (!spot) return null
  return (
    <span aria-hidden="true" className="key-hint" data-resting={resting ? '' : undefined} style={{ left: spot.x }}>
      <span className="key-hint-arrow" />
      <kbd key={spot.n} className="key-hint-key">{spot.n}</kbd>
    </span>
  )
}
