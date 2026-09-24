/**
 * Where a section's events happened, drawn only.
 *
 * Every number comes from lib/timelineLayout (the projection, the pin size, the
 * label spacing) and every colour from the theme, so this file decides nothing.
 * The land is Natural Earth's 1:50m outline from the backend's library.json.
 * A pin can hold several nearby places; pressing it again steps to its next
 * event, so every event there is one press away without a list.
 * `at` is the place lit: the chosen event's, or the step being read's.
 */
import { labelGap, labelText, pinsOf, placeLabels, projection } from '../lib/timelineLayout'

export default function TimelineMap({ section, library, accent, chosen, at, onPick }) {
  const view = library.map.views[section.map]
  if (!view) return null
  const { width, height, maxHeight, minHeight, font, pin, size, project } = projection(view)
  const pins = pinsOf(section, library.places)
  const sides = placeLabels(pins, at, project, { font, pin, width, height })
  const ring = (points) => points.map(([lon, lat]) => project({ lon, lat }).map((n) => n.toFixed(1)).join(',')).join(' ')
  const next = (p) => p.events[(p.events.indexOf(chosen?.id) + 1) % p.events.length]

  return (
    // Full width of the reader; the views are wide, so the drawing fills it
    // instead of leaving an empty band beside a tall narrow map.
    <figure className="w-full rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden m-0 bg-[var(--timeline-map-water)]">
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
              className="cursor-pointer"
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
