/**
 * Things on one winding vine, as many to a row as the width allows, curling
 * back when they run out of room (lib/vine.js). The vine draws itself on and
 * each thing pops in as it is reached (styles/grow.css). `items` are { key, node };
 * `from` grows the vine in from the left edge, off its group's bud.
 */
import config from '../../grow.json'
import { snake, vinePath } from '../../lib/vine'
import { useWidth } from './hooks'

const SIZE = config.vine

export default function Vine({ items, from = false }) {
  const [ref, width] = useWidth()
  const { spots, cw, height } = snake(items.length, width, SIZE)
  return (
    <div ref={ref} className="grow-vine" style={{ height: width ? height : SIZE.row }}>
      {width > 0 && (
        <>
          <svg className="grow-stem" width={width} height={height} aria-hidden="true">
            <path d={vinePath(spots, cw, from)} pathLength="1" />
          </svg>
          {items.map((item, k) => (
            <div key={item.key} className="grow-spot" style={{ left: spots[k].x, top: spots[k].y, '--k': k / items.length }}>
              {item.node}
            </div>
          ))}
        </>
      )}
    </div>
  )
}
