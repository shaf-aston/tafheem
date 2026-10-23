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
 *   nahw    chunky 3-D blocks       daleel  book under a lens
 *   dict    bookmarked lexicon      mem     a lawh, one line left blank
 *   quiz    question card           timelines  events along an arrow
 *   dawah   speech bubble, star     colloq  two speech bubbles
 *   kit     toolbox                 home    an open arch, a crescent over it
 *   similar two pages, one line apart
 *   jawhara  a cut jewel, one spark     wasitiyya  a line held between two bars
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
  jawhara: (
    <>
      <path d="M18 24l6-10h16l6 10-14 28z" {...ink} strokeWidth="2.4" />
      <path d="M18 24h28M24 14l8 38 8-38M28 24l4-10 4 10" {...ink} strokeWidth="1.6" />
      <path className="em-star" d="M50 8l1.6 3.4 3.4 1.6-3.4 1.6L50 18l-1.6-3.4L45 13l3.4-1.6z" fill="currentColor" />
    </>
  ),
  wasitiyya: (
    <>
      <path d="M14 12h36M14 52h36" {...ink} strokeWidth="3" />
      <path d="M20 12v40M44 12v40" {...ink} strokeWidth="2" opacity=".5" />
      <path className="em-flicker" d="M32 18v28" {...ink} strokeWidth="3.4" />
      <circle cx="32" cy="32" r="4" fill="currentColor" />
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
  daleel: (
    <>
      <path d="M10 14h30v38H10z" fill="currentColor" opacity=".18" />
      <path d="M10 14h30v38H10zM16 24h18M16 31h18M16 38h10" {...ink} strokeWidth="2.2" />
      <g className="em-lift">
        <circle cx="42" cy="40" r="10" fill="var(--surface)" />
        <circle cx="42" cy="40" r="10" {...ink} strokeWidth="3" />
        <path d="M49 47l9 9" {...ink} strokeWidth="4" />
      </g>
    </>
  ),
  dict: (
    <>
      <path d="M14 8h34a4 4 0 014 4v44H18a4 4 0 01-4-4z" fill="currentColor" opacity=".25" />
      <path d="M14 52V8h34a4 4 0 014 4v44H18a4 4 0 01-4-4zM14 52a4 4 0 014-4h34" {...ink} strokeWidth="2.4" />
      <path className="em-sway" d="M44 8v16l-4-3-4 3V8" fill="currentColor" />
      <text x="30" y="40" textAnchor="middle" fontSize="16" fontWeight="700" fill="currentColor" fontFamily="var(--font-arabic)">ع</text>
    </>
  ),
  // The board a child learns hifz on: lines written out, one left blank to fill (the tab's gaps).
  similar: (
    <>
      <rect x="10" y="14" width="26" height="36" rx="3" {...ink} strokeWidth="2.4" />
      <rect className="em-sway" x="28" y="14" width="26" height="36" rx="3" fill="currentColor" opacity=".18" stroke="currentColor" strokeWidth="2.4" />
      <path d="M15 24h16M15 32h16M15 40h10" {...ink} strokeWidth="2.2" />
      <path d="M33 24h16M33 40h16" {...ink} strokeWidth="2.2" />
      <path d="M33 32h9" stroke="currentColor" strokeWidth="3.4" strokeLinecap="round" />
    </>
  ),
  mem: (
    <>
      <path d="M12 20h40v36a4 4 0 01-4 4H16a4 4 0 01-4-4z" fill="currentColor" opacity=".2" />
      <path d="M12 20h40v36a4 4 0 01-4 4H16a4 4 0 01-4-4zM24 20v-6a8 8 0 0116 0v6" {...ink} strokeWidth="2.6" />
      <circle cx="32" cy="14" r="2.4" fill="currentColor" />
      <path d="M19 30h26M19 38h7M38 38h7M19 46h26M19 54h14" {...ink} strokeWidth="2.6" />
      <path className="em-rays" d="M29 38h6" {...ink} strokeWidth="2.6" strokeDasharray="1 3" />
    </>
  ),
  quiz: (
    <>
      <rect x="10" y="10" width="44" height="44" rx="10" fill="currentColor" opacity=".2" />
      <rect x="10" y="10" width="44" height="44" rx="10" {...ink} strokeWidth="2.4" />
      <path className="em-lift" d="M25 26a7 7 0 1110 6c-2 1-3 3-3 5v2" {...ink} strokeWidth="3.4" />
      <circle cx="32" cy="46" r="2.4" fill="currentColor" />
    </>
  ),
  timelines: (
    <>
      {/* An arrow, so time reads as moving one way, and four events taking
          turns above and below it. Three marks hung evenly off a bar, as this
          once was, read as a ceiling lamp. */}
      <path d="M4 33h52M54 28l6 5-6 5" {...ink} strokeWidth="2.4" />
      <path d="M10 33V21M23 33v12M36 33V21M49 33v12" {...ink} strokeWidth="1.6" opacity=".6" />
      <rect x="4" y="13" width="12" height="7" rx="2" fill="currentColor" opacity=".35" />
      <rect x="17" y="46" width="12" height="7" rx="2" fill="currentColor" opacity=".35" />
      <rect x="30" y="13" width="12" height="7" rx="2" fill="currentColor" opacity=".35" />
      <rect x="43" y="46" width="12" height="7" rx="2" fill="currentColor" opacity=".35" />
      <circle cx="10" cy="33" r="3.5" fill="currentColor" />
      <circle cx="23" cy="33" r="3.5" fill="currentColor" />
      <circle className="em-lift" cx="36" cy="33" r="4.5" fill="currentColor" />
      <circle cx="49" cy="33" r="3.5" fill="currentColor" />
    </>
  ),
  dawah: (
    <>
      <path d="M8 14h40a4 4 0 014 4v22a4 4 0 01-4 4H24l-10 9v-9H8a4 4 0 01-4-4V18a4 4 0 014-4z" fill="currentColor" opacity=".2" />
      <path d="M8 14h40a4 4 0 014 4v22a4 4 0 01-4 4H24l-10 9v-9H8a4 4 0 01-4-4V18a4 4 0 014-4z" {...ink} strokeWidth="2.4" />
      <path className="em-star" d="M28 21l2.4 4.4 5 .6-3.6 3.4 1 5L28 32l-4.8 2.4 1-5-3.6-3.4 5-.6z" fill="currentColor" />
      <path className="em-rays" d="M56 10l4-4M58 20h4" {...ink} strokeWidth="2" />
    </>
  ),
  colloq: (
    <>
      <path d="M6 10h30a4 4 0 014 4v16a4 4 0 01-4 4H18l-8 7v-7H6a4 4 0 01-4-4V14a4 4 0 014-4z" fill="currentColor" opacity=".55" />
      <path className="em-lift em-late" d="M58 26H30a4 4 0 00-4 4v14a4 4 0 004 4h16l8 7v-7h4a4 4 0 004-4V30a4 4 0 00-4-4z" {...ink} strokeWidth="2.4" />
      <path d="M33 37h22M33 42h14" {...ink} strokeWidth="2" opacity=".6" />
    </>
  ),
  home: (
    <>
      <path d="M14 58V32a18 18 0 0136 0v26z" fill="currentColor" opacity=".2" />
      <path d="M14 58V32a18 18 0 0136 0v26M6 58h52" {...ink} strokeWidth="2.6" />
      <path d="M25 58V40a7 7 0 0114 0v18" {...ink} strokeWidth="2.2" />
      <path className="em-rays" d="M34 3a5 5 0 100 9 4 4 0 110-9z" fill="currentColor" />
    </>
  ),
  kit: (
    <>
      <path d="M24 20v-6a3 3 0 013-3h10a3 3 0 013 3v6" {...ink} strokeWidth="2.4" />
      <rect x="6" y="20" width="52" height="34" rx="5" fill="currentColor" opacity=".22" />
      <rect x="6" y="20" width="52" height="34" rx="5" {...ink} strokeWidth="2.4" />
      <path d="M6 34h52" {...ink} strokeWidth="2" />
      <rect className="em-lift" x="27" y="30" width="10" height="8" rx="2" fill="currentColor" />
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
