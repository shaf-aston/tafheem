/**
 * Home's hint for the number keys: a faded keycap under the strip, its arrow
 * pointing up at a tab, hopping 1 → 2 → … along every tab on show. The motion
 * says "press this number for this tab" with no words; hovering the strip
 * brings it up clear. Look in styles/components.css (.key-hint).
 */
import { useEffect, useRef, useState } from 'react'

import { motionOff } from '../../lib/motion'
import { motion } from '../../theme'

// `strip` is the tablist.
export default function KeyHint({ strip }) {
  const [spot, setSpot] = useState(null)
  const at = useRef(0)

  useEffect(() => {
    // Its number is the tab's place in the strip (the key that opens it), so a
    // tab a narrow screen hides is skipped, never renumbered.
    const hop = () => {
      const tabs = [...(strip.current?.children ?? [])]
      if (!tabs.some((tab) => tab.offsetWidth > 0)) return
      let n = at.current % tabs.length
      while (tabs[n].offsetWidth === 0) n = (n + 1) % tabs.length
      const tab = tabs[n]
      setSpot({ n: n + 1, x: tab.offsetLeft + tab.offsetWidth / 2 })
      at.current = n + 1
    }
    hop()
    if (motionOff()) return undefined
    const timer = setInterval(hop, motion['key-hint-ms'])
    return () => clearInterval(timer)
  }, [strip])

  if (!spot) return null
  return (
    <span aria-hidden="true" className="key-hint" style={{ left: spot.x }}>
      <span className="key-hint-arrow" />
      <kbd key={spot.n} className="key-hint-key">{spot.n}</kbd>
    </span>
  )
}
