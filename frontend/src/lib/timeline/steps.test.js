import { describe, expect, it } from 'vitest'
import settings from '../../timelines.json'
import { pinsOf } from './map'
import { canFold, pathRows, placeOfStep, readingOrder, stepIds } from './steps'

const { steps: STEPS } = settings

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

  it('finds matching ids at every depth', () => {
    const run = [st('a'), st('b', { steps: [st('m', { aside: true }), st('n')] }), st('c', { aside: true })]
    expect(stepIds(run, (s) => s.aside)).toEqual(['m', 'c'])
    expect(stepIds(run, canFold)).toEqual(['b', 'm', 'c'])
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
