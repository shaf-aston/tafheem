import { describe, expect, it } from 'vitest'

import { ayahEnd } from './ayahEnd'

describe('ayahEnd', () => {
  it('closes an ayah with the medallion and Arabic-Indic digits, ungrouped', () => {
    expect(ayahEnd(7)).toBe('۝٧')
    expect(ayahEnd(218)).toBe('۝٢١٨')
    expect(ayahEnd(1000)).toBe('۝١٠٠٠')
  })
})
