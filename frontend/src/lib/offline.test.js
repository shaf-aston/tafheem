import { describe, expect, it } from 'vitest'

import { coreLine, packState, sizeLabel } from './offline'

describe('offline', () => {
  it('says sizes the way a phone does', () => {
    expect(sizeLabel(2_532_682)).toBe('2.5 MB')
    expect(sizeLabel(300_400)).toBe('300 KB')
    expect(sizeLabel(12)).toBe('1 KB')
  })

  it('calls a pack ready only when every file is saved', () => {
    expect(packState(7, 7)).toBe('ready')
    expect(packState(3, 7)).toBe('none')
    expect(packState(0, 0)).toBe('none')
  })

  it('fills the core size into its line', () => {
    expect(coreLine(2_175_005)).toContain('2.2 MB')
  })
})
