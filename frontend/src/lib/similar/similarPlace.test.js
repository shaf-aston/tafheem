import { describe, expect, it } from 'vitest'

import { parsePlace } from './similarPlace'

describe('parsePlace', () => {
  it('reads a verse', () => {
    expect(parsePlace('2:3')).toEqual({ surah: 2, ayah: 3 })
  })

  it('is null for nothing, a surah alone, or an ayah the surah does not have', () => {
    expect(parsePlace(null)).toBeNull()
    expect(parsePlace('2')).toBeNull()
    expect(parsePlace('2:999')).toBeNull()
    expect(parsePlace('bukhari/1')).toBeNull()
  })
})
