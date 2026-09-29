import { describe, expect, it } from 'vitest'

import { familyOf, leadGrade, topicOf } from './hadithGrade'

describe('familyOf', () => {
  it('puts each wording in its family, weak words winning', () => {
    expect(familyOf('Sahih').id).toBe('sound')
    expect(familyOf('Hasan Sahih').id).toBe('sound')
    expect(familyOf('Hasan').id).toBe('good')
    expect(familyOf('Very Daif').id).toBe('weak')
    expect(familyOf('Daif Isnaad').id).toBe('weak')
    expect(familyOf('Mawdu').id).toBe('weak')
  })
  it('names no family for a wording it does not know', () => {
    expect(familyOf('Isnaad Unknown')).toBe(null)
  })
})

describe('leadGrade', () => {
  const grades = [{ by: 'Zubair Ali Zai', grade: 'Hasan' }, { by: 'Al-Albani', grade: 'Sahih' }]
  it('leads with the first scholar in the config who graded it', () => {
    expect(leadGrade(grades)).toEqual({ by: 'Al-Albani', grade: 'Sahih' })
  })
  it('falls back to whoever graded it', () => {
    expect(leadGrade([{ by: 'Someone', grade: 'Hasan' }])).toEqual({ by: 'Someone', grade: 'Hasan' })
  })
  it('reads an ungraded hadith of a Sahih collection as sahih by that collection, else nothing', () => {
    expect(leadGrade([], 'Sahih Muslim')).toEqual({ by: 'Sahih Muslim', grade: 'Sahih' })
    expect(leadGrade([])).toBe(null)
  })
})

describe('topicOf', () => {
  it('lets the specific topic win over the general one', () => {
    expect(topicOf('The Book of Prayer - Funerals')).toBe('funeral')
    expect(topicOf('Penalty of Hunting while on Pilgrimage')).toBe('hajj')
    expect(topicOf('Virtues of the Qur\'an')).toBe('quran')
    expect(topicOf('Distribution of Water')).toBe('trade')
    expect(topicOf('The Book of Water')).toBe('purify')
    expect(topicOf('Prayer at Night (Tahajjud)')).toBe('prayer')
  })
  it('names nothing for a book no word matches', () => {
    expect(topicOf('Kafeel')).toBe(null)
  })
})
