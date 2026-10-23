import { describe, expect, it } from 'vitest'
import settings from '../../timelines.json'
import { pinsOf, placeLabels, projection } from './map'

const ev = (id, at, more = {}) => ({ id, at, ...more })
const { map: MAP } = settings

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
