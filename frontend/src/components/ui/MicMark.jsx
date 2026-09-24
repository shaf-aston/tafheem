/**
 * The capsule microphone: the mark that means dictation.
 *
 * The studio mic everyone recognises: capsule, three grille slits, cradle arc,
 * stem. Every place you speak instead of type shows this, and only this file
 * knows its shape.
 *
 * It takes no colour: everything strokes in `currentColor`, so it picks up the
 * text colour of whatever it sits in. Its three states are the three a
 * microphone has, and each is a different kind of motion rather than a faster
 * one:
 *   idle       still. On hover, after a beat, the grille pulses very slowly:
 *              the recording motion previewed, not a second idea
 *   recording  the grille slits pulse like a level meter
 *   thinking   the cradle arc becomes a chasing dash; the capsule stays still,
 *              so it never reads as listening
 *
 * The states are a `data-state` attribute and nothing more. Every stroke and
 * animation is a CSS consequence of it (see index.css), and the numbers behind
 * them are theme.json's `mic` group, so retuning the mark is a config edit and
 * not a code change.
 *
 * Hovering: the delay is `animation-delay` in CSS, not a timer here, so there
 * is nothing to leak on unmount. It only fires inside a `.mic-host`, the
 * caller's own hit area, because the mark is smaller than the control it sits
 * in and hovering the control should be enough.
 */
export default function MicMark({ state = 'idle', size = 22, className = '' }) {
  return (
    <svg
      className={`mic-mark ${className}`}
      data-state={state}
      viewBox="0 0 24 24"
      width={size}
      height={size}
      aria-hidden="true"
    >
      <rect x="9" y="2.5" width="6" height="11" rx="3" />
      <g className="mic-grille">
        <line x1="10.8" y1="6" x2="13.2" y2="6" />
        <line x1="10.8" y1="8" x2="13.2" y2="8" />
        <line x1="10.8" y1="10" x2="13.2" y2="10" />
      </g>
      <path className="mic-arc" d="M5.5 11 a6.5 6.5 0 0 0 13 0" />
      <line x1="12" y1="17.5" x2="12" y2="21" />
    </svg>
  )
}
