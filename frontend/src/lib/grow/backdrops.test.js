import { describe, expect, it } from 'vitest'

import config from '../../config/worlds.json'
import { BACKDROPS, SUBJECTS, backdropOf } from './backdrops'

describe('the backdrop manifest', () => {
  it.each(Object.entries(BACKDROPS))('%s says what it shows, who made it and what lets us use it', (id, entry) => {
    expect(entry.file).toBeTruthy()
    expect(SUBJECTS).toContain(entry.subject)
    expect(entry.credit).toBeTruthy()
    expect(entry.licence).toBeTruthy()
  })

  it('has every backdrop a world names', () => {
    const named = config.worlds.filter((world) => world.backdrop).map((world) => world.backdrop)
    expect(named.length).toBeGreaterThan(0)
    for (const id of named) expect(BACKDROPS, id).toHaveProperty(id)
  })
})

describe('backdropOf', () => {
  it('gives the urls of a backdrop that exists', () => {
    const courtyard = backdropOf('courtyard')
    expect(courtyard.image).toBe('/grow/backdrops/courtyard.svg')
    expect(courtyard.poster).toBe('/grow/backdrops/courtyard.svg')
    expect(courtyard.video).toBeUndefined()
  })

  it('is null for no id and for one the manifest lacks', () => {
    expect(backdropOf(undefined)).toBeNull()
    expect(backdropOf('nowhere')).toBeNull()
  })
})
