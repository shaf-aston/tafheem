/**
 * The map: a view's drawing box, one pin per place visited, and where each
 * pin's name fits. Pure: the component only draws what this returns.
 */
import settings from '../../config/timelines.json'
import { readingOrder } from './steps'

const { map: MAP } = settings

/** The lon/lat box the land is drawn over: as far as a view can be widened. */
export function landBounds(land) {
  const lons = land.flat().map(([lon]) => lon)
  return { west: Math.min(...lons), east: Math.max(...lons) }
}

/**
 * The view widened east and west to fill a box `aspect` times as wide as it is
 * tall, about its middle where the land allows, slid along where one side runs
 * out, and never past the land there is to draw. A wide screen sees more of the
 * real map, rather than the same map cropped top and bottom, which cut
 * Jerusalem and Abyssinia off the Seerah.
 */
export function fitView(view, aspect, bounds) {
  const wide = Math.min(aspect * (view.north - view.south), bounds.east - bounds.west)
  if (!(wide > view.east - view.west)) return view
  const west = Math.min(Math.max((view.west + view.east - wide) / 2, bounds.west), bounds.east - wide)
  return { ...view, west, east: west + wide }
}

/** A view's drawing box, and a function taking lon/lat into it. */
export function projection(view) {
  const k = MAP['px-per-degree']
  const width = (view.east - view.west) * k
  const height = (view.north - view.south) * k
  const font = height * MAP['font-per-height']
  const pin = height * MAP['pin-per-height']
  return {
    width,
    height,
    // The lower of a fixed cap and a share of the window, so the time bar under
    // it is on screen too. A short wide box is filled by fitView widening the
    // view, not by a small picture in a wide empty frame.
    maxHeight: `min(${MAP['max-rem']}rem, ${MAP['max-vh']}svh)`,
    minHeight: `${MAP['min-rem']}rem`,
    font,
    pin,
    // Every other drawn size, from the two above and the knobs.
    size: {
      hit: pin * MAP['hit-pins'],
      chosen: pin * MAP['chosen-pins'],
      pinStroke: pin * MAP['pin-stroke'],
      coastStroke: pin * MAP['coast-stroke'],
      halo: font * MAP.halo,
      baseline: font * MAP.baseline,
      route: pin * MAP['route-stroke'],
    },
    project: ({ lon, lat }) => [(lon - view.west) * k, (view.north - lat) * k],
  }
}

const apart = (a, b) => Math.hypot(a.lon - b.lon, a.lat - b.lat)

/**
 * One pin per spot the section visits, in the order first visited, carrying
 * every event there. Places closer than merge-deg share a pin, named after the
 * first: Makkah, Hira and Arafat drawn apart were three rings on one dot.
 */
export function pinsOf(section, places) {
  const pins = []
  for (const event of section.events) {
    // A step's own place gets a pin too, so the map can follow the steps.
    const keys = [event.place, ...readingOrder(event.steps).map((r) => r.step.place)]
    for (const key of new Set(keys)) {
      const place = places[key]
      if (!place) continue
      // Near any place already in the pin, not only its first: otherwise the same
      // places merge or split depending on the order the events are listed.
      let pin = pins.find((p) => p.places.some((k) => k === key || apart(places[k], place) < MAP['merge-deg']))
      if (!pin) pins.push(pin = { key, ...place, places: [], events: [] })
      if (!pin.places.includes(key)) pin.places.push(key)
      if (!pin.events.includes(event.id)) pin.events.push(event.id)
    }
  }
  return pins
}

/**
 * Where each pin's name goes: 'right', 'left', or absent when neither side is
 * free. The chosen pin is placed first, and named even when crowded; then the
 * rest in order. A side is free
 * when its box (a width guessed from the letters) covers no other pin and no
 * name already placed, and stays inside the drawing's `width` and `height`. All sizes are
 * drawing units, as `project` gives.
 */
export function placeLabels(pins, chosenPlace, project, { font, pin, width, height }) {
  const chosenFirst = [...pins].sort((a, b) => b.places.includes(chosenPlace) - a.places.includes(chosenPlace))
  const dots = pins.map((p) => ({ key: p.key, at: project(p) }))
  const placed = []
  const sides = new Map()
  const overlaps = (a, b) => a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2
  for (const p of chosenFirst) {
    const [x, y] = project(p)
    const w = labelText(p).length * font * MAP['char-width']
    const gap = labelGap(pin)
    for (const side of ['right', 'left']) {
      const x1 = side === 'right' ? x + gap : x - gap - w
      const box = { x1, x2: x1 + w, y1: y - font * MAP.ascent, y2: y + font * MAP.descent }
      const r = pin * MAP['chosen-pins']
      const hitsDot = dots.some((d) => d.key !== p.key
        && overlaps(box, { x1: d.at[0] - r, x2: d.at[0] + r, y1: d.at[1] - r, y2: d.at[1] + r }))
      const inside = box.x1 >= 0 && box.x2 <= width && box.y1 >= 0 && box.y2 <= height
      if (inside && !hitsDot && placed.every((b) => !overlaps(box, b))) {
        placed.push(box)
        sides.set(p.key, side)
        break
      }
    }
    // The chosen place is always named, even over a neighbour: it is what the
    // reader is looking at.
    if (!sides.has(p.key) && p.places.includes(chosenPlace)) sides.set(p.key, 'right')
  }
  return sides
}

/** How far a name sits from its pin's centre, shared with the drawing. */
export const labelGap = (pin) => pin * MAP['label-gap']

/** A pin's printed name. No event count: a bare number beside a town read as noise. */
export const labelText = (p) => p.name
