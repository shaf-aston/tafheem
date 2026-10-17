/**
 * A world's faded backdrop: a still, or a short loop while motion is on, laid
 * under the world's content (.grow-backdrop, styles/growWorlds.css; how faint
 * is theme.json grow.backdrop-opacity). The picture is picked by id from
 * public/grow/backdrops/manifest.json through lib/backdrops.js; an id the
 * manifest lacks draws nothing, so a world may name one before it exists.
 *
 * The world screen mounts `<Backdrop id={world.backdrop} />` as the first child
 * of its screen, which wears .grow-world so the layer has something to fill.
 * With the reader's reduce-motion setting on, or the Animations switch off
 * (lib/motion.js), a loop is shown as its poster instead, so nothing moves.
 */
import { backdropOf } from '../../lib/backdrops'
import { motionOff } from '../../lib/motion'

export default function Backdrop({ id }) {
  const backdrop = backdropOf(id)
  if (!backdrop) return null
  const { image, video, poster } = backdrop
  const loop = video && !motionOff()
  return (
    <div className="grow-backdrop" data-subject={backdrop.subject} aria-hidden="true">
      {loop
        ? <video src={video} poster={poster} autoPlay muted loop playsInline />
        : <img src={image} alt="" />}
    </div>
  )
}
