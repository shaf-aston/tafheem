import { describe, expect, it } from 'vitest'

import { runs, toneOf, told, withoutMarks } from './rijal'

describe('runs', () => {
  it('opens on a name at the very start', () => {
    expect(runs('مالك قال', [[0, 4, 7]])).toEqual([{ text: 'مالك', id: 7 }, { text: ' قال' }])
  })

  it('keeps two names side by side apart', () => {
    expect(runs('abcd', [[0, 2, 1], [2, 4, 2]])).toEqual([{ text: 'ab', id: 1 }, { text: 'cd', id: 2 }])
  })

  it('finds the same name twice', () => {
    expect(runs('x ab y ab', [[2, 4, 5], [7, 9, 5]])).toEqual([
      { text: 'x ' }, { text: 'ab', id: 5 }, { text: ' y ' }, { text: 'ab', id: 5 },
    ])
  })

  it('ignores a range outside the string', () => {
    expect(runs('abc', [[10, 14, 3]])).toEqual([{ text: 'abc' }])
  })

  it('counts slices from the piece start when it begins mid-hadith', () => {
    expect(runs('cd ef', [[13, 15, 9]], 10)).toEqual([{ text: 'cd ' }, { text: 'ef', id: 9 }])
  })
})

describe('withoutMarks', () => {
  it('shifts slices left by the direction marks before them', () => {
    expect(withoutMarks('\u200fab \u200fcd', [[5, 7, 1]])).toEqual([[3, 5, 1]])
  })
})

describe('toneOf', () => {
  it('colours rank 1 trusted, rank 5 doubtful, and the rest and the unranked as danger', () => {
    expect([1, 3, 4, 5, 6, null].map(toneOf)).toEqual(['success', 'success', 'warn', 'warn', 'danger', 'danger'])
  })
})

describe('told', () => {
  // bukhari 4 opens with قال, which the chain walker cannot read; the name links can.
  const arabic = 'قَالَ ابْنُ شِهَابٍ وَأَخْبَرَنِي أَبُو سَلَمَةَ، أَنَّ جَابِرَ بْنَ عَبْدِ اللَّهِ، قَالَ "‏ بَيْنَا أَنَا أَمْشِي ‏". تَابَعَهُ يُونُسُ'
  const at = (s) => [arabic.indexOf(s), arabic.indexOf(s) + s.length]
  const names = [[...at('ابْنُ شِهَابٍ'), 1], [...at('أَبُو سَلَمَةَ'), 2], [...at('جَابِرَ بْنَ عَبْدِ اللَّهِ'), 3], [...at('يُونُسُ'), 4]]

  it('cuts at the last narrator named before the speech, and keeps his link and later ones', () => {
    const out = told(arabic, names)
    expect(out.text.startsWith('جَابِرَ')).toBe(true)
    expect(out.names.map((n) => n[2])).toEqual([3, 4])
    expect(out.text.slice(out.names[1][0], out.names[1][1])).toBe('يُونُسُ')
  })

  it('keeps the hadith whole, links and all, when nothing marks the cut', () => {
    const plain = 'قَالَ "‏ بَيْنَا ‏"'
    expect(told(plain, [])).toEqual({ text: plain, names: [] })
    expect(told(arabic, [names[2]]).text).toBe(arabic)
  })

  it('still uses the chain words where they read', () => {
    const out = told('حَدَّثَنَا زَيْدٌ عَنْ عَمْرٍو قَالَ "‏ صَلُّوا ‏"', [])
    expect(out.text.startsWith('عَنْ عَمْرٍو')).toBe(true)
  })
})
