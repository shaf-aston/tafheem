/**
 * Where everything on a timeline goes: step folding, map pins, addresses.
 *
 * Pure: no DOM, no React, no fetching. The components only draw this.
 */
import settings from '../timelines.json'

const { map: MAP, axis: AXIS, steps: STEPS } = settings

/** Every step and moment under an event, at any depth. */
export const countSteps = (steps = []) => steps.reduce((n, s) => n + 1 + countSteps(s.steps), 0)

/** A step worth folding: it holds moments, runs long, or is a side detail. */
export const canFold = (step) => (
  (step.steps ?? []).length > 0 || Boolean(step.aside) || step.summary.length >= STEPS['fold-from-chars']
)

/** The ids at any depth that pass `test`: which can fold, or which start folded. */
export const stepIds = (steps = [], test) => steps.flatMap((s) => [
  ...(test(s) ? [s.id] : []),
  ...stepIds(s.steps, test),
])

/** The flag that says a place is known from tradition; printed beside the place, not as a pill. */
export const TRAD = 'tradplace'

/** Every step at any depth in reading order, each with the steps it sits inside. */
export const readingOrder = (steps = [], above = []) => steps.flatMap((step) => [
  { step, above },
  ...readingOrder(step.steps, [...above, step]),
])

/** Where a step happened: its own place, else the nearest step above it with one, else the event's. */
export function placeOfStep(event, stepId) {
  const at = readingOrder(event.steps).find((r) => r.step.id === stepId)
  const chain = at ? [at.step, ...at.above.toReversed()] : []
  return chain.find((s) => s.place)?.place ?? event.place ?? null
}

/**
 * A run cut into rows: a lone step, or neighbouring steps that name a path,
 * read side by side as lanes. Lanes keep the order the data first names them
 * in, so reading order and drawn order agree. Each row carries its number:
 * lanes share one starting number, since they happen at the same time.
 */
export function pathRows(steps) {
  const rows = []
  let n = 1
  for (const step of steps) {
    const last = rows.at(-1)
    if (!step.path) {
      rows.push({ n, step })
      n += 1
    } else if (last?.lanes) {
      const lane = last.lanes.find((l) => l.path === step.path)
      if (lane) lane.steps.push(step)
      else last.lanes.push({ path: step.path, steps: [step] })
      n = last.n + Math.max(...last.lanes.map((l) => l.steps.length))
    } else {
      rows.push({ n, lanes: [{ path: step.path, steps: [step] }] })
      n += 1
    }
  }
  return rows
}

/** How wide the line's column is beside the opened event, as a CSS length. */
export const lineWidth = `${AXIS['width-rem']}rem`

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
    // In rem, not a share of the window: a cap in vh shrinks the drawing when
    // the window is short while the box around it keeps its width, and the map
    // ends up a small picture in a wide empty frame.
    maxHeight: `${MAP['max-rem']}rem`,
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

/**
 * A place in the tab as written after ?q=: "seerah", "seerah/hijrah", or
 * "seerah/badr/asbab/8:9" for one report on why an ayah came down.
 * Anything naming a section or event that does not exist is null, so a stale
 * link opens the tab plainly rather than half-open on nothing.
 */
export function parsePlace(q, sections) {
  if (!q) return null
  const [sectionId, eventId, word, ref, ...rest] = q.split('/')
  const section = sections.find((s) => s.id === sectionId)
  if (!section || rest.length) return null
  if (eventId === undefined) return { section: section.id, event: null, report: null }
  if (!section.events.some((e) => e.id === eventId)) return null
  if (word === undefined) return { section: section.id, event: eventId, report: null }
  if (word !== 'asbab' || !AYAH_REF.test(ref ?? '')) return null
  return { section: section.id, event: eventId, report: ref }
}

const AYAH_REF = /^\d+:\d+$/

/** The address of a place, the inverse of parsePlace. */
export const placeOf = (section, event, report) => (
  report ? `${section}/${event}/asbab/${report}` : event ? `${section}/${event}` : section
)

/**
 * The ayah a Qur'an reference opens on: the first of its range, or the first of
 * the surah. The Qur'an tab reads one ayah at a time (QuranLookup's AYAH_REF).
 */
export function firstAyah(ref) {
  const [surah, ayahs = '1'] = ref.split(':')
  return `${surah}:${ayahs.split('-')[0]}`
}
