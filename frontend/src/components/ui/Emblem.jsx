/**
 * A small hand-made picture for a world or a tab, one drawing style each so no two
 * sections feel cut from the same cloth (styles/emblem.css moves them; the Animations
 * switch stills them). Colour is the caller's --w, set on the wrapper; nothing here
 * has a colour of its own. An id with no picture draws nothing, so a new world may
 * name one before it exists.
 *
 *   words   flat cartoon sprout        fiqh    fine-line scales
 *   aqidah  geometric lantern          quran   soft-glow open book
 *   hadith  sketched scroll and pen    sarf    cartoon tree of letters
 *   nahw    chunky 3-D blocks
 */
const ink = { fill: 'none', stroke: 'currentColor', strokeLinecap: 'round', strokeLinejoin: 'round' }

const ART = {
  words: (
    <>
      <path d="M20 54h24l-3 8H23z" fill="currentColor" opacity=".85" />
      <path d="M32 54V32" {...ink} strokeWidth="3.5" />
      <path className="em-sway" d="M32 38c-12 0-16-9-16-15 11 0 16 6 16 15z" fill="currentColor" />
      <path className="em-sway em-late" d="M32 32c0-10 6-16 16-16 0 9-5 16-16 16z" fill="currentColor" opacity=".7" />
      <circle cx="26" cy="29" r="1.6" fill="var(--surface)" /><circle cx="44" cy="25" r="1.6" fill="var(--surface)" />
    </>
  ),
  fiqh: (
    <>
      <path d="M32 10v44M22 54h20" {...ink} strokeWidth="1.6" />
      <g className="em-tilt">
        <path d="M12 22h40" {...ink} strokeWidth="1.6" />
        <path d="M12 22l-6 14h12zM52 22l-6 14h12z" {...ink} strokeWidth="1.4" />
        <path d="M5 36a7 4 0 0014 0M45 36a7 4 0 0014 0" {...ink} strokeWidth="1.4" />
      </g>
      <circle cx="32" cy="9" r="2.4" fill="currentColor" />
    </>
  ),
  aqidah: (
    <>
      <path d="M32 6v8M24 14h16" {...ink} strokeWidth="2.4" />
      <path d="M22 18h20l6 12-6 22H22l-6-22z" {...ink} strokeWidth="2.4" />
      <path className="em-star" d="M32 26l2.6 4.6 5.2.6-3.8 3.6 1 5.2L32 37.4l-5 2.6 1-5.2-3.8-3.6 5.2-.6z" fill="currentColor" />
      <path d="M24 56h16" {...ink} strokeWidth="3" />
      <path className="em-flicker" d="M32 54c-2-2 0-4 0-6 2 2 2 4 0 6z" fill="currentColor" opacity=".6" />
    </>
  ),
  quran: (
    <>
      <g className="em-rays" {...ink} strokeWidth="2">
        <path d="M32 6v7M16 12l4 6M48 12l-4 6M7 26l7 2M57 26l-7 2" />
      </g>
      <path d="M8 24c9-3 17-2 24 3 7-5 15-6 24-3v28c-9-3-17-2-24 3-7-5-15-6-24-3z" fill="currentColor" opacity=".18" />
      <path d="M8 24c9-3 17-2 24 3 7-5 15-6 24-3v28c-9-3-17-2-24 3-7-5-15-6-24-3zM32 27v28" {...ink} strokeWidth="2.4" />
      <path d="M14 33c5-1 9 0 13 2M14 40c5-1 9 0 13 2M37 35c4-2 8-3 13-2M37 42c4-2 8-3 13-2" {...ink} strokeWidth="1.5" opacity=".6" />
    </>
  ),
  hadith: (
    <>
      <path className="em-draw" d="M16 12c-5 0-8 3-8 7v33c0 3 2 5 5 5h34c4 0 7-3 7-7V19c0-4-3-7-7-7z" {...ink} strokeWidth="2.2" strokeDasharray="3 3" />
      <path className="em-draw em-late" d="M18 24h28M18 32h24M18 40h27M18 48h14" {...ink} strokeWidth="2" strokeDasharray="2 3" />
      <g className="em-write">
        <path d="M44 56l12-26 5 3-12 25-6 1z" fill="currentColor" />
        <path d="M56 30l5 3" stroke="var(--surface)" strokeWidth="1.5" />
      </g>
    </>
  ),
  sarf: (
    <>
      <path d="M32 60V38M32 48c-7 0-11 4-13 9M32 52c7 0 10 3 13 7" {...ink} strokeWidth="3.2" />
      <circle className="em-sway" cx="32" cy="22" r="17" fill="currentColor" opacity=".3" />
      <circle className="em-sway em-late" cx="19" cy="31" r="10" fill="currentColor" opacity=".5" />
      <circle className="em-sway" cx="45" cy="31" r="10" fill="currentColor" opacity=".5" />
      <text x="32" y="29" textAnchor="middle" fontSize="15" fontWeight="700" fill="var(--text)" fontFamily="var(--font-arabic)">جذر</text>
    </>
  ),
  nahw: (
    <>
      <path className="em-lift" d="M4 42l14-7 14 7-14 7z" fill="currentColor" opacity=".6" />
      <path d="M4 42v10l14 7V49zM18 59V49l14-7v10z" fill="currentColor" opacity=".32" />
      <path className="em-lift em-late" d="M32 28l14-7 14 7-14 7z" fill="currentColor" />
      <path d="M32 28v10l14 7V35zM46 45V35l14-7v10z" fill="currentColor" opacity=".5" />
      <path d="M24 33l6-3" {...ink} strokeWidth="2.2" strokeDasharray="1 4" />
    </>
  ),
}

export default function Emblem({ id, size = 56, className = '' }) {
  const art = ART[id]
  if (!art) return null
  return (
    <svg className={`emblem em-${id} ${className}`} viewBox="0 0 64 64" width={size} height={size} aria-hidden="true" focusable="false">
      {art}
    </svg>
  )
}
