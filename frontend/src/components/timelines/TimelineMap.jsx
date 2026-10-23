/**
 * Where a section's events happened, drawn only.
 *
 * Every number comes from lib/timeline/map (the projection, the pin size, the
 * label spacing) and every colour from the theme, so this file decides nothing.
 * The land is Natural Earth's 1:50m outline from the backend's library.json.
 * A pin can hold several nearby places; pressing it again steps to its next
 * event, so every event there is one press away without a list.
 * `at` is the place lit: the chosen event's, or the step being read's.
 *
 * `upTo` is the event the time bar stands on. Places reached by then are drawn
 * full and joined by the route in the order visited, the last leg solid; places
 * not reached yet are faint. With nothing open, every place is drawn full.
 */
import { useLayoutEffect, useMemo, useRef, useState } from 'react'

import settings from '../../timelines.json'
import { fitView, labelGap, labelText, landBounds, pinsOf, placeLabels, projection } from '../../lib/timeline/map'
import { routeTo } from '../../lib/timeline/time'

const { map: MAP } = settings

export default function TimelineMap({ section, library, accent, chosen, at, upTo = null, onPick }) {
  const [box, aspect] = useBoxAspect()
  const bounds = useMemo(() => landBounds(library.map.land), [library.map.land])
  const given = library.map.views[section.map]
  if (!given) return null
  const view = aspect > 0 ? fitView(given, aspect, bounds) : given
  const { width, height, maxHeight, minHeight, font, pin, size, project } = projection(view)
  const pins = pinsOf(section, library.places)
  const sides = placeLabels(pins, at, project, { font, pin, width, height })
  const ring = (points) => points.map(([lon, lat]) => project({ lon, lat }).map((n) => n.toFixed(1)).join(',')).join(' ')
  const next = (p) => p.events[(p.events.indexOf(chosen?.id) + 1) % p.events.length]
  const order = new Map(section.events.map((e, i) => [e.id, i]))
  const reached = (p) => upTo === null || p.events.some((id) => order.get(id) <= upTo)
  const route = upTo === null ? [] : routeTo(section, upTo).filter((key) => library.places[key]).map((key) => project(library.places[key]))
  const line = (points) => points.map((pt) => pt.map((n) => n.toFixed(1)).join(',')).join(' ')

  return (
    // Full width of the reader; the views are wide, so the drawing fills it
    // instead of leaving an empty band beside a tall narrow map.
    // Never wider than the cap allows at this view's shape: where even the
    // widest view is narrower than the box, the map is framed and centred
    // rather than cropped, its edge the frame's.
    <figure ref={box} style={{ maxWidth: `calc(${maxHeight} * ${(width / height).toFixed(3)})` }} className="w-full mx-auto rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden m-0 bg-[var(--timeline-map-water)]">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="block w-full h-auto mx-auto"
        // Slice, not letterbox: on a phone the edges are cut, so names stay readable.
        preserveAspectRatio="xMidYMid slice"
        style={{ maxHeight, minHeight }}
        // A group, not an image: an image may not hold the pins' buttons.
        role="group"
        aria-label={`Map of ${section.name}`}
      >
        <rect x="0" y="0" width={width} height={height} fill="var(--timeline-map-water)" />
        {library.map.land.map((points, i) => (
          <polygon
            key={i}
            points={ring(points)}
            fill="var(--timeline-map-land)"
            stroke="var(--border-hi)"
            strokeWidth={size.coastStroke}
            strokeLinejoin="round"
          />
        ))}
        {route.length > 1 && (
          <g fill="none" stroke={accent} strokeWidth={size.route} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points={line(route.slice(0, -1))} strokeDasharray={`${size.route * MAP['route-dash']} ${size.route * MAP['route-dash']}`} opacity={MAP['route-past-opacity']} />
            <polyline points={line(route.slice(-2))} />
          </g>
        )}
        {pins.map((p) => {
          const [cx, cy] = project(p)
          const on = p.places.includes(at)
          const names = p.places.map((key) => library.places[key].name).join(', ')
          return (
            <g
              key={p.key}
              role="button"
              tabIndex={0}
              aria-label={p.events.length > 1
                ? `${names}: ${p.events.length} events, each press opens the next`
                : names}
              className="cursor-pointer tl-pin"
              opacity={reached(p) ? 1 : MAP['unseen-opacity']}
              onClick={() => onPick?.(next(p))}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onPick?.(next(p)) } }}
            >
              <title>{names}</title>
              {/* A wide invisible ring, so a small dot is still easy to press. */}
              <circle cx={cx} cy={cy} r={size.hit} fill="transparent" />
              <circle
                cx={cx}
                cy={cy}
                r={on ? size.chosen : pin}
                fill={on ? accent : 'var(--surface)'}
                stroke={accent}
                strokeWidth={size.pinStroke}
              />
              {sides.has(p.key) && (
                <text
                  x={sides.get(p.key) === 'right' ? cx + labelGap(pin) : cx - labelGap(pin)}
                  textAnchor={sides.get(p.key) === 'right' ? 'start' : 'end'}
                  y={cy + size.baseline}
                  fontSize={font}
                  fontWeight={on ? 600 : 400}
                  fill={on ? 'var(--text)' : 'var(--text-dim)'}
                  stroke="var(--timeline-map-land)"
                  strokeWidth={size.halo}
                  strokeLinejoin="round"
                  paintOrder="stroke"
                >
                  {labelText(p)}
                </text>
              )}
            </g>
          )
        })}
      </svg>
      {chosen && !at && (
        <figcaption className="w-0 min-w-full type-tiny text-[var(--text-faint)] px-3 py-2">
          No place is recorded for this event.
        </figcaption>
      )}
    </figure>
  )
}

/**
 * How many times wider than its tallest the map's box is, kept as it resizes:
 * the room around it (the frame is narrowed to the map, so not its own width) over the height the map may take (max-rem or max-vh,
 * whichever is lower, as projection's maxHeight says in CSS).
 */
function useBoxAspect() {
  const ref = useRef(null)
  const [value, setValue] = useState(0)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const read = () => {
      const rem = parseFloat(getComputedStyle(document.documentElement).fontSize)
      const cap = Math.min(MAP['max-rem'] * rem, (MAP['max-vh'] / 100) * window.innerHeight)
      setValue((el.parentElement ?? el).clientWidth / cap)
    }
    read()
    const watch = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(read)
    watch?.observe(el.parentElement ?? el)
    window.addEventListener('resize', read)
    return () => { watch?.disconnect(); window.removeEventListener('resize', read) }
  }, [])
  return [ref, value]
}
