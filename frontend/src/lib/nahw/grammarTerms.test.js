import { describe, expect, it } from 'vitest'

import config from '../../config/grammar.json'
import { caseGloss, posGloss, roleGloss } from './grammarTerms'

describe('English under an Arabic grammar tag', () => {
  it('names a role however it is vowelled, and a sister role by its job', () => {
    expect(roleGloss('فاعل')).toBe('doer')
    expect(roleGloss('نَائِبُ فَاعِلٍ')).toBe('stand-in doer')
    expect(roleGloss('اسم إن')).toBe('subject of inna')
    expect(roleGloss('خبر ليس')).toBe('news')
    expect(roleGloss('اسم كأن')).toBe('subject')
    expect(roleGloss('–')).toBe('')
    expect(roleGloss(undefined)).toBe('')
  })

  it('every case and type has its English, and a corpus code reads through its type', () => {
    for (const group of ['cases', 'types']) {
      for (const entry of Object.values(config[group])) expect(entry.en).toBeTruthy()
    }
    expect(caseGloss('mabni (سكون على اللام)')).toBe('fixed ending')
    expect(posGloss('N')).toBe('noun')
    expect(posGloss('??')).toBe('')
  })
})
