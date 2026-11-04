import { describe, expect, it } from 'vitest'

import { colorFor } from '../../theme'
import { accentOf, GROUPS, LISTED, TABS } from './tabs'
import Emblem from '../../components/ui/display/Emblem'
import vercel from '../../../../vercel.json'

describe('the tab registry', () => {
  it('has every tab served by the host at /<tab>', () => {
    const served = vercel.rewrites.map((rule) => rule.source).find((source) => source.startsWith('/:tab('))
    for (const tab of TABS) expect(served).toMatch(new RegExp(`[(|]${tab.id}[|)]`))
  })

  it('gives every tab its own id', () => {
    const ids = TABS.map((tab) => tab.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('gives every tab its own picture', () => {
    const emblems = TABS.map((tab) => tab.emblem)
    for (const tab of TABS) expect(Emblem({ id: tab.emblem }), tab.id).not.toBeNull()
    expect(new Set(emblems).size).toBe(emblems.length)
  })

  it('files every tab under a heading All sections has', () => {
    const groups = new Set(GROUPS.map((group) => group.id))
    for (const tab of TABS) expect(groups.has(tab.group), tab.id).toBe(true)
  })

  it('says in a line what every tab is for', () => {
    for (const tab of TABS) expect(tab.blurb?.length, tab.id).toBeLessThanOrEqual(60)
    for (const tab of TABS) expect(tab.blurb, tab.id).toBeTruthy()
  })

  it('opens on Home, which is browsable', () => {
    expect(TABS[0].id).toBe('home')
    expect(LISTED[0].id).toBe('home')
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
