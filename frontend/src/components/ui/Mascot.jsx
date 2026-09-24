/**
 * Qalam (قَلَم), a reed pen that reacts to what the app is doing.
 *
 * It takes no colour: it inherits `--c`, the accent of whichever tab it is
 * sitting in, so it matches every panel without being told about any of them.
 * Sizes, timings and captions come from mascot.json. The only thing this file
 * decides is the shape of the pen.
 */
import { captionFor, sizeRem } from '../../lib/mascot'

export default function Mascot({ mood = 'idle', place = 'header', caption = false, className = '' }) {
  const label = captionFor(mood)
  const rem = sizeRem(place)

  return (
    <div className={`flex flex-col items-center gap-1.5 ${className}`}>
      {/* The viewBox is cropped to the pen itself, with room either side for the
          moods that swing it. A square box would letterbox a tall thin pen down
          to a sliver, so height drives the size and width follows the shape. */}
      <svg
        className="qalam"
        data-mood={mood}
        data-place={place}
        viewBox="26 6 76 136"
        style={{ height: `${rem}rem`, width: 'auto' }}
        role="img"
        aria-label={`Qalam: ${label}`}
      >
        {/* The resting tilt lives on this outer group, as a plain SVG attribute.
            A CSS `transform` animation on the same element replaces the
            attribute outright rather than adding to it, so every mood's motion
            has to sit one level in, otherwise the tilt was lost for as long as
            any mood animation ran, and each mood rotated around the wrong point
            (SVG's default transform-origin, not the nib). */}
        {/* The ink the nib leaves while sweeping on hover. It sits outside the
            rotation because ink stays on the page once written, and before the
            pen so the pen passes over it. Its curve is the arc the nib tip
            actually travels, measured from the sweep's pivot, not drawn by
            eye, so the stroke appears exactly under the moving nib. */}
        <path className="qalam-ink" d="M72.5 114.5 Q64 118.6 54 118" />

        <g transform="rotate(-12 64 118)">
          {/* Rotated about the nib tip so every mood's motion pivots where a
              real pen touches the page. */}
          <g className="qalam-pen">
            <path className="qalam-barrel" d="M52 28 a12 12 0 0 1 24 0 l-2 58 h-20 z" />
            <path className="qalam-shine" d="M57.5 33 v50" />
            <rect className="qalam-band" x="52.5" y="84.5" width="23" height="7" rx="2" />
            <path className="qalam-nib" d="M54.5 91 h19 l-4.5 21 -5 6 -6.5 -8 z" />
            <path className="qalam-slit" d="M64 96 v18" />

            <circle className="qalam-eye" cx="58.5" cy="52" r="3.6" />
            <circle className="qalam-eye" cx="70" cy="52" r="3.6" />
            <path className="qalam-mouth" d="M58.5 62 q5.5 5 11 0" />
          </g>
        </g>

        {/* Sits outside the rotation so it always falls straight down. */}
        <circle className="qalam-drop" cx="60" cy="124" r="5" />
      </svg>

      {caption && (
        <p className="type-small text-[var(--text-faint)] text-center" aria-live="polite">
          {label}
        </p>
      )}
    </div>
  )
}
