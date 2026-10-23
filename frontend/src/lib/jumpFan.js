/**
 * The jump fan: hold the phone's current tab and three places rise above the
 * thumb (Top, Back, Bottom). Slide onto one, let go, the page goes there.
 * Back is where the page was before the last jump, so a trip to the top costs
 * nothing; it is only offered once there is somewhere to go back to.
 */
import { useRef, useState } from 'react'

import theme from '../theme.json'
import { glideTo } from './scrollToEl'

const PRESS_MS = theme.motion['press-ms']

// Top to bottom on screen, as the fan draws them.
export const JUMPS = [
  { id: 'top', label: 'Top' },
  { id: 'back', label: 'Back' },
  { id: 'bottom', label: 'Bottom' },
]

/** Where a jump lands: `back` the saved place (null when none), `end` the page's last scroll. */
export const landing = (id, back, end) => ({ top: 0, back, bottom: end })[id]

/** The choice under the finger at `y`: the box it is in, else the nearest one, else none below the fan. */
export function pickAt(y, boxes) {
  if (!boxes.length || y > boxes.at(-1).bottom) return null
  const near = boxes.reduce((b, box) => (Math.abs(y - mid(box)) < Math.abs(y - mid(b)) ? box : b))
  return near.id
}
const mid = (box) => (box.top + box.bottom) / 2

/** Press, hold and slide on a tab. `bind` goes on the tab; `fan` is the open fan's x and lit choice, or null. */
export function useJumpFan() {
  const [fan, setFan] = useState(null)
  const back = useRef(null)
  const press = useRef({ timer: 0, open: false })
  const list = useRef(null)

  const boxes = () => [...(list.current?.children ?? [])].map((el) => ({ id: el.dataset.jump, ...el.getBoundingClientRect().toJSON() }))
  const usable = (id) => id !== 'back' || back.current != null

  const bind = {
    onPointerDown(e) {
      if (e.button) return
      e.currentTarget.setPointerCapture?.(e.pointerId)
      const x = e.clientX
      press.current.open = false
      press.current.timer = setTimeout(() => {
        press.current.open = true
        navigator.vibrate?.(8)
        setFan({ x, lit: null })
      }, PRESS_MS)
    },
    onPointerMove(e) {
      if (!press.current.open) return
      const lit = pickAt(e.clientY, boxes().filter((b) => usable(b.id)))
      setFan((f) => (f && f.lit !== lit ? { ...f, lit } : f))
    },
    onPointerUp(e) {
      clearTimeout(press.current.timer)
      if (!press.current.open) return
      const lit = pickAt(e.clientY, boxes().filter((b) => usable(b.id)))
      setFan(null)
      if (!lit) return
      const top = landing(lit, back.current, document.documentElement.scrollHeight - innerHeight)
      back.current = globalThis.scrollY
      glideTo(top)
    },
    onPointerCancel() {
      clearTimeout(press.current.timer)
      setFan(null)
    },
    // A held press is the fan's, not a tap and not the phone's own menu.
    onClickCapture(e) { if (press.current.open) { press.current.open = false; e.stopPropagation(); e.preventDefault() } },
    onContextMenu: (e) => e.preventDefault(),
  }

  return { bind, fan, list, usable }
}
