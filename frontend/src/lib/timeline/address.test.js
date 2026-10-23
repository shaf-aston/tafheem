import { describe, expect, it } from 'vitest'
import { nameOfPlace, parsePlace, placeOf } from './address'

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

describe('nameOfPlace', () => {
  const sections = [{ id: 'signs', name: 'Signs of the Hour', events: [{ id: 'coming', title: "The Prophet's coming" }] }]

  it.each([
    ['signs', 'Signs of the Hour'],
    ['signs/coming', "The Prophet's coming"],
    ['signs/coming/asbab/8:9', "The Prophet's coming 8:9"],
    ['signs/gone', 'signs/gone'],
  ])('%s reads %s', (q, name) => {
    expect(nameOfPlace(q, sections)).toBe(name)
  })
})
