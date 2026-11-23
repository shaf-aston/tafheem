import { describe, expect, it } from 'vitest'

import { matched, pageLines, shorter } from './pageLines'

const texts = (lines) => lines.map((line) => line.text)
const words = (n, w = 'كلمة') => Array.from({ length: n }, () => w).join(' ')

describe('pageLines', () => {
  it('joins a sentence the printed page broke, and cuts at each full stop', () => {
    const page = 'كان العلماء يرحلون في طلب العلم من بلد\nإلى بلد. وقد كتب البخاري صحيحه\nفي ست عشرة سنة. فأي همة؟ إن طلب العلم عبادة!'
    expect(texts(pageLines(page))).toEqual([
      'كان العلماء يرحلون في طلب العلم من بلد إلى بلد.',
      'وقد كتب البخاري صحيحه في ست عشرة سنة.',
      'فأي همة؟',
      'إن طلب العلم عبادة!',
    ])
  })

  it('keeps the printed lines of a paragraph with no full stop: a poem, a chat, headings', () => {
    expect(texts(pageLines('باب الطهارة\nباب الصلاة'))).toEqual(['باب الطهارة', 'باب الصلاة'])
  })

  it('numbers each line by its paragraph', () => {
    expect(pageLines('قال الشيخ.\n\nنعم.').map((line) => line.paragraph)).toEqual([0, 1])
  })

  it('has nothing to say of an empty page', () => {
    expect(pageLines('  \n\n ')).toEqual([])
  })
})

describe('shorter', () => {
  it('leaves a sentence that fits', () => {
    expect(shorter('ذهب الولد إلى المدرسة', 4)).toEqual(['ذهب الولد إلى المدرسة'])
  })

  it('cuts a long sentence at its commas, gathering short clauses together', () => {
    expect(shorter('قال، نعم، ذهب الولد إلى المدرسة، ثم رجع', 4))
      .toEqual(['قال، نعم،', 'ذهب الولد إلى المدرسة،', 'ثم رجع'])
  })

  it('with no comma, cuts before a joining word standing alone, vowelled or not', () => {
    expect(shorter('صلى الرجل في المسجد ثُمَّ خرج إلى السوق', 4)).toEqual(['صلى الرجل في المسجد', 'ثُمَّ خرج إلى السوق'])
  })

  it('never cuts at a word that only starts like one (ثمرة is not ثم)', () => {
    expect(shorter('أكل الرجل ثمرة طيبة من الشجرة الكبيرة', 4)).toEqual(['أكل الرجل ثمرة طيبة', 'من الشجرة الكبيرة'])
  })

  it('as a last resort cuts into even pieces, losing and reordering nothing', () => {
    const lines = shorter(words(10), 4)
    expect(lines.map((line) => line.split(' ').length)).toEqual([3, 4, 3])
    expect(lines.join(' ')).toBe(words(10))
  })
})

describe('matched', () => {
  it("keeps the page's own words and marks, pairing the translator's reading in order", () => {
    const words = [{ arabic: 'قال', english: 'said' }, { arabic: 'الولد', english: 'the boy' }]
    const out = matched('قَالَ، الولد.', words)
    expect(out.map(({ before, core, after }) => before + core + after).join(' ')).toBe('قَالَ، الولد.')
    expect(out.map((one) => one.word?.english)).toEqual(['said', 'the boy'])
    expect(out[0].word.arabic).toBe('قَالَ')
  })

  it('leaves a word the translator skipped as plain text, and carries on after it', () => {
    const out = matched('«قال» يا ولد', [{ arabic: 'قال' }, { arabic: 'ولد' }])
    expect(out.map((one) => Boolean(one.word))).toEqual([true, false, true])
    expect(out[0].before).toBe('«')
  })
  it("pairs the Qur'an's own spelling with plain print (ٱ, the dagger alef)", () => {
    const words = [{ arabic: 'ٱلْحَمْدُ' }, { arabic: 'لِلَّهِ' }, { arabic: 'ٱلرَّحْمَٰنِ' }]
    expect(matched('الحمد لله الرحمن', words).every((one) => one.word)).toBe(true)
  })
})

describe('pageLines and its marks', () => {
  it('reads a Latin question mark as an end, and a number as no end', () => {
    expect(texts(pageLines('هل أنت هنا? نعم'))).toEqual(['هل أنت هنا?', 'نعم'])
    expect(texts(pageLines('سعره 3.5\nدينار'))).toEqual(['سعره 3.5', 'دينار'])
  })
})
