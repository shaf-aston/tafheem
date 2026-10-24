import { describe, expect, it } from 'vitest'
import { eventIcon, sectionLook } from './look'

describe('section and event looks', () => {
  it('gives each named section its own look and an unlisted one the fallback', () => {
    expect(sectionLook('seerah').icon).toBe('dome')
    expect(sectionLook('nope')).toEqual(sectionLook('unknown'))
  })

  it('cycles event pictures without running off the end', () => {
    expect(eventIcon(0)).toBe(eventIcon(6))
    expect(eventIcon(7)).toBe(eventIcon(1))
  })
})
