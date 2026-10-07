/**
 * Swipe sideways to step through anything with a previous and a next: a finger
 * on a phone, a quick mouse flick or two fingers on a trackpad on a computer.
 * Spread the returned props on the element the gesture belongs to. Swiping
 * left goes next, as a page turns. A falsy step (at either end) does nothing.
 *
 * Under a finger the part marked data-slide (useSlide below) follows it, and
 * holds back at either end, so a swipe feels like moving the thing itself.
 */
import { useRef, useState } from 'react'

const DRAG = 60        // px sideways before a drag counts
const FLICK_MS = 300   // a slower mouse drag is selecting text, not swiping
const WHEEL = 80       // px of trackpad scroll sideways before it counts
const SETTLE_MS = 250  // quiet that ends one trackpad gesture, so its glide steps once
const FOLLOW = 0.4     // how far the content moves for each px the finger does
const END = 0.12       // the same, at an end where there is nothing to step to

/** 1 for next, -1 for previous, 0 for not a swipe. */
export function swipeOf({ dx, dy, ms = 0, mouse = false }) {
  if (Math.abs(dx) < DRAG || Math.abs(dx) < 2 * Math.abs(dy)) return 0
  if (mouse && ms > FLICK_MS) return 0
  return dx < 0 ? 1 : -1
}

// Sideways already means something in a text box or a sideways scroller.
function claimed(target, root) {
  for (let el = target; el && el !== root; el = el.parentElement) {
    if (el.matches('input, textarea, select, [contenteditable="true"]')) return true
    if (el.scrollWidth > el.clientWidth && /auto|scroll/.test(getComputedStyle(el).overflowX)) return true
  }
  return false
}

export function useSwipe(onPrev, onNext) {
  const start = useRef(null)
  const swiped = useRef(false)
  const wheel = useRef({ sum: 0, done: false, timer: 0 })
  // The content back where it belongs, gliding unless it is about to be replaced.
  const settle = (face) => {
    if (!face) return
    face.style.transition = 'translate calc(var(--motion-base-ms) * 1ms) ease-out'
    face.style.translate = ''
  }
  const go = (way) => {
    const step = way > 0 ? onNext : onPrev
    if (step) step()
  }

  return {
    // Vertical scrolling and pinch stay the browser's; sideways comes here.
    style: { touchAction: 'pan-y pinch-zoom' },
    onPointerDown: (e) => {
      swiped.current = false
      start.current = e.button === 0 && !claimed(e.target, e.currentTarget)
        ? { x: e.clientX, y: e.clientY, t: e.timeStamp, face: e.pointerType !== 'mouse' && (e.currentTarget.querySelector('[data-slide]') ?? e.currentTarget) }
        : null
    },
    onPointerMove: (e) => {
      const s = start.current
      if (!s?.face) return
      const dx = e.clientX - s.x
      const sideways = Math.abs(dx) > 2 * Math.abs(e.clientY - s.y)
      const step = dx < 0 ? onNext : onPrev
      s.face.style.transition = 'none'
      s.face.style.translate = sideways ? `${dx * (step ? FOLLOW : END)}px` : ''
    },
    onPointerUp: (e) => {
      const s = start.current
      start.current = null
      if (!s) return
      settle(s.face)
      const mouse = e.pointerType === 'mouse'
      const way = swipeOf({ dx: e.clientX - s.x, dy: e.clientY - s.y, ms: e.timeStamp - s.t, mouse })
      if (!way) return
      if (mouse) window.getSelection()?.removeAllRanges()
      swiped.current = true
      go(way)
    },
    onPointerCancel: () => { settle(start.current?.face); start.current = null },
    // A picture dragged by the mouse would start the browser's own drag and cancel the swipe.
    onDragStart: (e) => e.preventDefault(),
    // The click a mouse swipe ends with is not a press of whatever it ended on.
    onClickCapture: (e) => {
      if (!swiped.current) return
      swiped.current = false
      e.stopPropagation()
      e.preventDefault()
    },
    onWheel: (e) => {
      const w = wheel.current
      clearTimeout(w.timer)
      w.timer = setTimeout(() => { w.sum = 0; w.done = false }, SETTLE_MS)
      if (w.done || e.ctrlKey || Math.abs(e.deltaX) <= Math.abs(e.deltaY)) return
      if (claimed(e.target, e.currentTarget)) return
      w.sum += e.deltaX
      if (Math.abs(w.sum) < WHEEL) return
      w.done = true
      go(w.sum > 0 ? 1 : -1)
    },
  }
}

/**
 * Props for the part that changes as `at` steps: it comes in from the side it was
 * asked for, and is what a finger drags. Give the same element key={at}.
 */
export const slideWay = (from, to) => (to === from ? '' : to > from ? 'slide-next' : 'slide-prev')

export function useSlide(at) {
  const [seen, setSeen] = useState({ at, way: '' })
  let way = seen.way
  if (seen.at !== at) {
    way = slideWay(seen.at, at)
    setSeen({ at, way })
  }
  return { className: way, 'data-slide': '' }
}
