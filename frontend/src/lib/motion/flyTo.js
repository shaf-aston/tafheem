import { motionOff } from './motion'

/**
 * A copy of `from` flies to the middle of `to`, shrinking and fading as it
 * lands, then is gone. The quiz's right answer, carried up to the word it means.
 *
 * Drawn as a fixed copy over the page, so nothing on the page moves or reflows;
 * the real option stays where it was. Runs on transform and opacity only, over
 * the spring token, and not at all with Animations off or reduce-motion on.
 * Resolves when the copy has landed (at once when it never flew).
 */
export function flyTo(from, to) {
  if (!from || !to || motionOff()) return Promise.resolve()
  const a = from.getBoundingClientRect()
  const b = to.getBoundingClientRect()
  const ghost = from.cloneNode(true)
  ghost.setAttribute('aria-hidden', 'true')
  Object.assign(ghost.style, {
    position: 'fixed', left: `${a.left}px`, top: `${a.top}px`, width: `${a.width}px`, height: `${a.height}px`,
    margin: '0', pointerEvents: 'none', zIndex: 'var(--z-pop, 50)',
  })
  document.body.append(ghost)
  const dx = b.left + b.width / 2 - (a.left + a.width / 2)
  const dy = b.top + b.height / 2 - (a.top + a.height / 2)
  const css = getComputedStyle(document.documentElement)
  const flight = ghost.animate([
    { transform: 'none', opacity: 1 },
    { transform: `translate(${dx}px, ${dy}px) scale(0.6)`, opacity: 0 },
  ], {
    duration: Number(css.getPropertyValue('--motion-spring-ms')) || 0,
    easing: css.getPropertyValue('--motion-slide-ease').trim() || 'ease-out',
  })
  return flight.finished.catch(() => {}).finally(() => {
    ghost.remove()
    // The word it means takes the catch: one small swell, on the same spring.
    to.animate([{ transform: 'none' }, { transform: 'scale(1.08)' }, { transform: 'none' }], {
      duration: Number(css.getPropertyValue('--motion-spring-ms')) || 0,
      easing: css.getPropertyValue('--motion-spring-ease').trim() || 'ease-out',
    })
  })
}
