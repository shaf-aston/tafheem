/**
 * The map behind WordPicture's country spots: every outline in the board's view,
 * the board's own countries a shade stronger, so the game's countries stand out from
 * the neighbours without saying which is which. Outlines: lib/colloquial/countryShapes.json.
 */
import shapes from '../../../../lib/colloquial/countryShapes.json'
import { touches } from '../../../../lib/colloquial/countryMap'

const { countries } = shapes

export default function MapArt({ view, keys }) {
  const unit = view[2] / 100
  return (
    <g strokeLinejoin="round" strokeWidth={unit * 0.35}>
      {Object.entries(countries).filter(([, c]) => touches(c.box, view)).map(([code, c]) => (
        <path key={code} d={c.d} data-key={keys.includes(code) ? code : undefined}
          fill={keys.includes(code) ? 'color-mix(in oklab, var(--primary) 22%, var(--surface-hi))' : 'var(--surface)'}
          stroke="var(--border-hi)" />
      ))}
    </g>
  )
}
