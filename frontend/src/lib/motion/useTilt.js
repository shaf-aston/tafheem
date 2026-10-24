/**
 * Props that make a card lean toward a mouse (the .tilt class in styles/motion.css).
 * Writes the pointer's place on the card as --tx and --ty, each -1 to 1; the
 * CSS turns them into a lean of at most motion.tilt-max-deg. Touch and pen never
 * tilt, and nothing moves while the Animations switch or reduce-motion is on.
 */
import { motionOff } from './motion'

const lean = (event) => {
  const box = event.currentTarget.getBoundingClientRect()
  const at = (pos, start, size) => Math.max(-1, Math.min(1, ((pos - start) / size) * 2 - 1))
  return [at(event.clientX, box.left, box.width), at(event.clientY, box.top, box.height)]
}

export function useTilt() {
  return {
    onPointerMove(event) {
      if (event.pointerType !== 'mouse' || motionOff()) return
      const [x, y] = lean(event)
      event.currentTarget.style.setProperty('--tx', x.toFixed(2))
      event.currentTarget.style.setProperty('--ty', y.toFixed(2))
    },
    onPointerLeave(event) {
      event.currentTarget.style.removeProperty('--tx')
      event.currentTarget.style.removeProperty('--ty')
    },
  }
}
