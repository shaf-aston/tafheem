import { motionOff } from './motion'

/**
 * `el` opens out of `from`: it starts as small as the tile that was pressed, sitting on it and
 * turned away, then swings round and grows into its own place, a flip. Transform and opacity
 * only, over the enter token and the settle curve, turned `--motion-open-deg` away at the start
 * and seen through the tilt's perspective; nothing at all with Animations off or reduce-motion on.
 *
 * Call it before the first paint (a layout effect): the move is drawn over the layout, which it
 * never changes, so the page can scroll to `el`'s real place while it plays.
 */
export function openFrom(el, from) {
  if (!el?.animate || !from || motionOff()) return
  const css = getComputedStyle(document.documentElement)
  const number = (name) => Number(css.getPropertyValue(name))
  const a = from.getBoundingClientRect()
  const b = el.getBoundingClientRect()
  const dx = a.left + a.width / 2 - (b.left + b.width / 2)
  const dy = a.top + a.height / 2 - (b.top + b.height / 2)
  const small = Math.min(a.width / b.width, a.height / b.height)
  const lens = `perspective(${number('--motion-tilt-perspective-px')}px)`
  el.style.backfaceVisibility = 'hidden'
  el.animate([
    { transform: `translate(${dx}px, ${dy}px) ${lens} rotateY(${number('--motion-open-deg')}deg) scale(${small})`, opacity: 0.4 },
    { transform: `translate(0, 0) ${lens} rotateY(0deg) scale(1)`, opacity: 1 },
  ], {
    duration: number('--motion-enter-ms'),
    easing: css.getPropertyValue('--motion-settle-ease').trim() || 'ease-out',
  })
}
