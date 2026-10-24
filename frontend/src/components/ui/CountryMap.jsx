/**
 * A small map of where something is spoken or found: its countries in the
 * card's hue among faint neighbours, with a dot on each named city.
 *
 * CountryMap is the picture; CountryIcons is the row of tiny flags with
 * names that says which countries, for a card's side. Both take ISO alpha-2
 * codes, so the places live in data (colloquial/dialects.json), not here.
 * The flags are data/countryFlags.json (scripts/countryFlags.mjs).
 * The outlines are data/countryShapes.json (scripts/countryShapes.mjs); land
 * and borders wear the Timelines map's colours, so every map reads alike.
 */
import { useId } from 'react'

import flagFile from '../../data/countryFlags.json'
import shapes from '../../data/countryShapes.json'
import { project, touches, viewOf } from '../../lib/shell/countryMap'

const { countries } = shapes
const { flags } = flagFile
const tint = (hue, pct) => `color-mix(in oklab, ${hue} ${pct}%, transparent)`
// 4 wide to 3 high: the Arab world is wide, and a square left Fusha's map a strip.
const ASPECT = 4 / 3

/**
 * codes: ['EG']; cities: [{ name, at: [lon, lat] }]. Decorative: the words
 * beside it name the place. The neighbours fade out towards the frame, so the
 * map has no hard edge on the card; its own countries never fade.
 */
export function CountryMap({ codes = [], cities = [], hue, className = '' }) {
  const fade = useId()
  const own = codes.map((c) => countries[c]).filter(Boolean)
  const dots = cities.map((c) => ({ ...c, xy: project(c.at) }))
  const view = viewOf(own.map((c) => c.box), dots.map((c) => c.xy), { aspect: ASPECT })
  if (!view) return null
  const unit = view[2] / 100
  const around = Object.entries(countries).filter(([code, c]) => !codes.includes(code) && touches(c.box, view))
  return (
    <svg viewBox={view.join(' ')} aria-hidden="true" preserveAspectRatio="xMidYMid meet" className={`aspect-[4/3] ${className}`}>
      <defs>
        {/* An alpha mask: only the stops' opacity counts, not their colour. */}
        <radialGradient id={`${fade}g`}>
          <stop offset="0.6" stopColor="var(--text)" />
          <stop offset="1" stopColor="var(--text)" stopOpacity="0" />
        </radialGradient>
        <mask id={fade} style={{ maskType: 'alpha' }}><rect x={view[0]} y={view[1]} width={view[2]} height={view[3]} fill={`url(#${fade}g)`} /></mask>
      </defs>
      <g strokeLinejoin="round" strokeWidth={unit * 0.6}>
        <g mask={`url(#${fade})`}>
          {around.map(([code, c]) => (
            <path key={code} d={c.d} fill="var(--surface-hi)" stroke="var(--border-hi)" />
          ))}
        </g>
        {own.map((c) => <path key={c.name} d={c.d} fill={tint(hue, 55)} stroke={hue} />)}
      </g>
      {dots.map((c) => (
        <circle key={c.name} cx={c.xy[0]} cy={c.xy[1]} r={unit * 2.6} fill="var(--text)" stroke="var(--surface)" strokeWidth={unit * 1.2} />
      ))}
    </svg>
  )
}

// A flag the size of a letter; as an image, so no two flags' inner ids can collide.
function Flag({ code }) {
  if (!flags[code]) return null
  return (
    <img src={`data:image/svg+xml,${encodeURIComponent(flags[code])}`} alt="" aria-hidden="true"
      className="h-2.5 aspect-[3/2] shrink-0 rounded-[2px] shadow-[0_0_0_1px_var(--border)]" />
  )
}

/** Each country as a tiny flag and its name; past `most`, only how many, as the map beside it shows which. */
export function CountryIcons({ codes = [], most = 4 }) {
  const known = codes.filter((c) => countries[c])
  if (known.length > most) return <span className="type-small text-[var(--text-faint)]">{known.length} countries</span>
  return (
    <ul className="flex flex-wrap gap-x-3 gap-y-1 type-small text-[var(--text-faint)]">
      {known.map((code) => (
        <li key={code} className="flex items-center gap-1.5">
          <Flag code={code} />
          {countries[code].name}
        </li>
      ))}
    </ul>
  )
}
