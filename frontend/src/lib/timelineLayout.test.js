import { describe, expect, it } from 'vitest'
import settings from '../timelines.json'
import {
  canFold, countSteps, firstAyah, parsePlace, pathRows, pinsOf, placeLabels, placeOf, placeOfStep, projection,
  readingOrder, stepIds,
} from './timelineLayout'

const ev = (id, at, more = {}) => ({ id, at, ...more })
const { map: MAP, steps: STEPS } = settings

describe('map', () => {
  const view = { west: 30, north: 30, east: 40, south: 20 }
  const places = {
    makkah: { name: 'Makkah', lon: 39.83, lat: 21.42 },
    hira: { name: 'Hira', lon: 39.86, lat: 21.46 },
    madinah: { name: 'Madinah', lon: 39.61, lat: 24.47 },
  }

  it('projects the view corners onto the drawing box', () => {
    const { width, height, project } = projection(view)
    expect([width, height]).toEqual([10 * MAP['px-per-degree'], 10 * MAP['px-per-degree']])
    expect(project({ lon: 30, lat: 30 })).toEqual([0, 0])
    expect(project({ lon: 40, lat: 20 })).toEqual([width, height])
  })

  it('sizes pins and text by the view height, so a wider view keeps the same text size', () => {
    const tall = projection(view)
    const wide = projection({ ...view, east: 50 })
    expect(wide.font).toBe(tall.font)
    expect(tall.size.chosen).toBe(tall.pin * MAP['chosen-pins'])
    // The press ring must reach past the chosen dot, or a chosen pin is harder to press.
    expect(tall.size.hit).toBeGreaterThan(tall.size.chosen)
  })

  it('makes one pin per place, carrying every event there', () => {
    const pins = pinsOf({ events: [ev('birth', 1, { place: 'makkah' }), ev('x', 2), ev('fath', 3, { place: 'makkah' })] }, places)
    expect(pins).toHaveLength(1)
    expect(pins[0].events).toEqual(['birth', 'fath'])
  })

  // One drawing unit per degree, text 10 units tall, pins 1 unit: easy to reason about.
  const flat = ({ lon, lat }) => [lon, 100 - lat]
  const size = { font: 10, pin: 1, width: 100, height: 100 }
  const pin = (key, lon, lat, n = 1) => ({ key, name: key, lon, lat, places: [key], events: Array(n).fill(key) })

  it('puts a name on the right, and on the left when a neighbour takes the right', () => {
    expect([...placeLabels([pin('a', 50, 50)], null, flat, size)]).toEqual([['a', 'right']])
    const sides = placeLabels([pin('a', 50, 50), pin('b', 55, 50)], null, flat, size)
    expect(sides.get('a')).toBe('left')
  })

  it('leaves a name off when neither side is free, and keeps the chosen pin named', () => {
    const crowd = [pin('a', 50, 50), pin('b', 45, 50), pin('c', 55, 50)]
    expect(placeLabels(crowd, null, flat, size).has('a')).toBe(false)
    expect(placeLabels(crowd, 'a', flat, size).has('a')).toBe(true)
  })

  it('never places a name outside the drawing', () => {
    expect(placeLabels([pin('edge', 98, 50)], null, flat, size).get('edge')).toBe('left')
    expect(placeLabels([pin('wide', 20, 50)], null, flat, { ...size, width: 45 }).has('wide')).toBe(false)
    expect(placeLabels([pin('top', 50, 99)], null, flat, size).has('top')).toBe(false)
  })

  it('merges places closer than merge-deg into one pin, and keeps one just past it apart', () => {
    const gap = MAP['merge-deg']
    const two = (d) => pinsOf(
      { events: [ev('a', 1, { place: 'one' }), ev('b', 2, { place: 'two' }), ev('c', 3, { place: 'one' })] },
      { one: { name: 'One', lon: 40, lat: 20 }, two: { name: 'Two', lon: 40 + d, lat: 20 } },
    )
    const merged = two(gap - 0.01)
    expect(merged).toHaveLength(1)
    expect(merged[0]).toMatchObject({ key: 'one', places: ['one', 'two'], events: ['a', 'b', 'c'] })
    expect(two(gap + 0.01)).toHaveLength(2)
  })

  it('merges a chain of near places the same way whatever order they come in', () => {
    const d = MAP['merge-deg'] * 0.9
    const chain = { a: { name: 'A', lon: 40, lat: 20 }, b: { name: 'B', lon: 40 + d, lat: 20 }, c: { name: 'C', lon: 40 + 2 * d, lat: 20 } }
    const count = (order) => pinsOf({ events: order.map((k, i) => ev(k, i, { place: k })) }, chain).length
    expect(count(['a', 'b', 'c'])).toBe(1)
    expect(count(['b', 'a', 'c'])).toBe(1)
  })

  it('names a merged pin after its first place, whichever place is chosen', () => {
    const pins = pinsOf({ events: [ev('a', 1, { place: 'makkah' }), ev('b', 2, { place: 'hira' }), ev('c', 3, { place: 'madinah' })] }, places)
    expect(pins.map((p) => [p.key, p.places])).toEqual([['makkah', ['makkah', 'hira']], ['madinah', ['madinah']]])
  })
})

describe('parsePlace', () => {
  const sections = [{ id: 'seerah', events: [{ id: 'hijrah' }, { id: 'badr' }] }]

  it('reads a section, a section with an event, and one report on an ayah', () => {
    expect(parsePlace('seerah', sections)).toEqual({ section: 'seerah', event: null, report: null })
    expect(parsePlace('seerah/hijrah', sections)).toEqual({ section: 'seerah', event: 'hijrah', report: null })
    expect(parsePlace('seerah/badr/asbab/8:9', sections)).toEqual({ section: 'seerah', event: 'badr', report: '8:9' })
  })

  it.each([
    '', null, 'nowhere', 'seerah/nothing', 'seerah/hijrah/extra', '/hijrah',
    'seerah/badr/asbab', 'seerah/badr/asbab/eight', 'seerah/badr/asbab/8:9/more',
  ])('refuses %j', (q) => {
    expect(parsePlace(q, sections)).toBeNull()
  })

  it('writes back what it reads, with and without a report', () => {
    expect(parsePlace(placeOf('seerah', 'hijrah'), sections)).toEqual({ section: 'seerah', event: 'hijrah', report: null })
    expect(parsePlace(placeOf('seerah', 'badr', '8:9'), sections)).toEqual({ section: 'seerah', event: 'badr', report: '8:9' })
  })
})

describe('firstAyah', () => {
  it.each([['2:30-37', '2:30'], ['9:40', '9:40'], ['105', '105:1']])('%s opens on %s', (ref, ayah) => {
    expect(firstAyah(ref)).toBe(ayah)
  })
})

describe('step folding', () => {
  const st = (id, more = {}) => ({ id, summary: 'short', ...more })
  const long = 'x'.repeat(STEPS['fold-from-chars'])

  it('folds a step with moments, a long one, or an aside, and nothing else', () => {
    expect(canFold(st('a', { steps: [st('m')] }))).toBe(true)
    expect(canFold(st('b', { summary: long }))).toBe(true)
    expect(canFold(st('c', { aside: true }))).toBe(true)
    expect(canFold(st('d'))).toBe(false)
    expect(canFold(st('e', { summary: long.slice(1), steps: [] }))).toBe(false)
  })

  it('finds matching ids at every depth, and counts every step and moment', () => {
    const run = [st('a'), st('b', { steps: [st('m', { aside: true }), st('n')] }), st('c', { aside: true })]
    expect(stepIds(run, (s) => s.aside)).toEqual(['m', 'c'])
    expect(stepIds(run, canFold)).toEqual(['b', 'm', 'c'])
    expect(countSteps(run)).toBe(5)
    expect(countSteps(undefined)).toBe(0)
  })
})

describe('walking the steps', () => {
  const st = (id, more = {}) => ({ id, summary: 's', ...more })
  const event = {
    id: 'musa',
    place: 'egypt',
    steps: [st('river'), st('flight', { place: 'madyan', steps: [st('well'), st('bush', { place: 'sinai' })] }), st('sea')],
  }

  it('reads depth first and knows what each step sits inside', () => {
    const order = readingOrder(event.steps)
    expect(order.map((r) => r.step.id)).toEqual(['river', 'flight', 'well', 'bush', 'sea'])
    expect(order[2].above.map((s) => s.id)).toEqual(['flight'])
    expect(readingOrder(undefined)).toEqual([])
  })

  it('takes the nearest place: own, then the step above, then the event', () => {
    expect(placeOfStep(event, 'bush')).toBe('sinai')
    expect(placeOfStep(event, 'well')).toBe('madyan')
    expect(placeOfStep(event, 'sea')).toBe('egypt')
    expect(placeOfStep(event, 'nowhere')).toBe('egypt')
    expect(placeOfStep({ id: 'x', steps: [st('a')] }, 'a')).toBe(null)
  })

  it('puts step places on the map once per event', () => {
    const places = { egypt: { name: 'Egypt', lon: 31, lat: 30 }, sinai: { name: 'Sinai', lon: 34, lat: 28.5 },
      madyan: { name: 'Madyan', lon: 35, lat: 28.4 } }
    const pins = pinsOf({ events: [event] }, places)
    expect(pins.map((p) => p.key)).toEqual(['egypt', 'madyan', 'sinai'])
    expect(pins.every((p) => p.events.length === 1)).toBe(true)
  })
})

describe('side by side paths', () => {
  const st = (id, path) => ({ id, summary: 's', ...(path && { path }) })

  it('groups neighbouring path steps into lanes that share a number', () => {
    const rows = pathRows([st('angel'), st('b1', 'believer'), st('d1', 'disbeliever'), st('b2', 'believer'), st('end')])
    expect(rows.map((r) => r.n)).toEqual([1, 2, 4])
    expect(rows[1].lanes.map((l) => [l.path, l.steps.map((s) => s.id)]))
      .toEqual([['believer', ['b1', 'b2']], ['disbeliever', ['d1']]])
    expect(rows[2].step.id).toBe('end')
  })

  it('leaves a run with no paths as plain numbered steps', () => {
    expect(pathRows([st('a'), st('b')]).map((r) => [r.n, r.step.id])).toEqual([[1, 'a'], [2, 'b']])
    expect(pathRows([])).toEqual([])
  })
})
