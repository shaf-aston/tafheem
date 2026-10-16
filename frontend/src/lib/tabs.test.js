import { describe, expect, it } from 'vitest'

import { colorFor } from '../theme'
import { accentOf, GROUPS, LISTED, TABS } from './tabs'

describe('the tab registry', () => {
  it('gives every tab its own id', () => {
    const ids = TABS.map((tab) => tab.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('gives every tab its own one-letter mark', () => {
    const marks = TABS.map((tab) => tab.mark)
    for (const mark of marks) expect(mark).toBeTruthy()
    expect(new Set(marks).size).toBe(marks.length)
  })

  it('files every tab under a heading All sections has', () => {
    const groups = new Set(GROUPS.map((group) => group.id))
    for (const tab of TABS) expect(groups.has(tab.group), tab.id).toBe(true)
  })

  it('leaves a hidden tab out of everything a person browses', () => {
    expect(LISTED.some((tab) => tab.hidden)).toBe(false)
    expect(LISTED).toHaveLength(TABS.filter((tab) => !tab.hidden).length)
  })
})

describe('a tab\'s colour', () => {
  it('is the theme\'s colour for that tab', () => {
    for (const tab of TABS) expect(accentOf(tab.id), tab.id).toBe(colorFor('tab', tab.id))
    expect(accentOf('dict')).not.toBe(accentOf('quran'))
  })

  it('falls back to the theme\'s default for a tab it has no colour for', () => {
    expect(accentOf('no-such-tab')).toBe(colorFor('tab', 'default'))
  })
})
