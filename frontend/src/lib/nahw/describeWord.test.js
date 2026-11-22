import { describe, expect, it } from 'vitest'

import { describeWord } from './describeWord'
import { UNNAMED, caseLabel, roleGloss } from './grammarTerms'

const words = [
  { word: 'كَتَبَ', role: 'فعل ماض', role_key: 'fil', case: 'mabni', sign: 'مبني على الفتح' },
  { word: 'الطالبُ', role: 'فاعل', role_key: 'fail', case: "raf'", sign: 'الضمة', governor: 0 },
  { word: 'المجتهدُ', role: 'نعت', role_key: 'sifah', case: "raf'", sign: 'الضمة', follows: 1 },
]

describe('describeWord', () => {
  it('names the role, preferring the fuller name', () => {
    expect(describeWord(words[1]).label).toBe('فاعل')
    expect(describeWord({ ...words[1], name: 'فاعل مرفوع' }).label).toBe('فاعل مرفوع')
    expect(describeWord(words[1]).hasRole).toBe(true)
    expect(describeWord({ word: 'x' }).hasRole).toBe(false)
    expect(describeWord({ word: 'x' }).label).toBeUndefined()
  })

  it('glosses the name first, the role when the name has none', () => {
    expect(describeWord(words[1]).roleGloss).toBe(roleGloss('فاعل'))
    expect(describeWord({ ...words[1], name: 'zzz' }).roleGloss).toBe(roleGloss('فاعل'))
    // the fuller name's gloss wins over the role's when it has one
    const named = describeWord({ ...words[1], role: 'خبر', name: 'اسم كأن' })
    expect(named.roleGloss).toBe('subject')
    expect(named.roleGloss).not.toBe(roleGloss('خبر'))
  })

  it('marks a word the analyser would not name', () => {
    expect(describeWord({ word: 'x', role: UNNAMED }).unnamed).toBe(true)
    expect(describeWord(words[0]).unnamed).toBe(false)
  })

  it('colours by role_key, grey without one', () => {
    expect(describeWord(words[1]).color).toBe('var(--role-fail)')
    expect(describeWord({ word: 'x' }).color).toBe('var(--role-default)')
  })

  it('gives the case in Arabic, its gloss and the one reading', () => {
    const d = describeWord(words[1])
    expect(d.caseText).toBe(caseLabel("raf'"))
    expect(d.caseGloss).not.toBe('')
    expect(d.reading).toEqual([caseLabel("raf'"), 'الضمة'])
    expect(describeWord({ word: 'x' })).toMatchObject({ caseText: '', caseGloss: '', reading: [] })
  })

  it('says a built word once', () => {
    const d = describeWord(words[0])
    expect(d.reading).toEqual(['مبني على الفتح'])
  })

  it('finds the governor, or the word followed', () => {
    expect(describeWord(words[1], words)).toMatchObject({ headIndex: 0, head: words[0], follows: false })
    expect(describeWord(words[2], words)).toMatchObject({ headIndex: 1, head: words[1], follows: true })
  })

  it('has no head when nothing governs it, or the head is missing', () => {
    expect(describeWord(words[0], words)).toMatchObject({ headIndex: undefined, head: null, follows: false })
    // index known but no sentence given, or out of range
    expect(describeWord(words[1])).toMatchObject({ headIndex: 0, head: null })
    expect(describeWord({ word: 'x', governor: 9 }, words).head).toBeNull()
  })

  it('treats governor 0 as a head, not as none', () => {
    expect(describeWord({ word: 'x', governor: 0, follows: 2 }, words).headIndex).toBe(0)
  })
})
