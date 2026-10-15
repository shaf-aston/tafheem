import { describe, expect, it } from 'vitest'

import { drawnChain, runs, toneOf, told, withoutMarks } from './rijal'

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

  it("marks the name alone where sunnah.com's link takes in the collector's aside (Abu Dawud 1, Muslim 126)", () => {
    const linked = (text, shown) => [[text.indexOf(shown), text.indexOf(shown) + shown.length, 4]]
    const first = 'حَدَّثَنَا عَبْدُ الْعَزِيزِ، - يَعْنِي ابْنَ مُحَمَّدٍ - عَنْ'
    expect(runs(first, linked(first, 'عَبْدُ الْعَزِيزِ، - يَعْنِي ابْنَ مُحَمَّدٍ'))).toEqual([
      { text: 'حَدَّثَنَا ' }, { text: 'عَبْدُ الْعَزِيزِ', id: 4 }, { text: '، - يَعْنِي ابْنَ مُحَمَّدٍ - عَنْ' },
    ])
    const after = 'حَدَّثَنَا - وَكِيعٌ، عَنْ'
    expect(runs(after, linked(after, '- وَكِيعٌ'))).toEqual([
      { text: 'حَدَّثَنَا - ' }, { text: 'وَكِيعٌ', id: 4 }, { text: '، عَنْ' },
    ])
  })

  it('leaves a name with no aside mark as linked, comma and all', () => {
    const text = 'عَنْ أَبِيهِ، قَالَ'
    const at = text.indexOf('أَبِيهِ،')
    expect(runs(text, [[at, at + 'أَبِيهِ،'.length, 2]])).toEqual([{ text: 'عَنْ ' }, { text: 'أَبِيهِ،', id: 2 }, { text: ' قَالَ' }])
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
    const out = told(arabic, null, names)
    expect(out.text.startsWith('جَابِرَ')).toBe(true)
    expect(out.names.map((n) => n[2])).toEqual([3, 4])
    expect(out.text.slice(out.names[1][0], out.names[1][1])).toBe('يُونُسُ')
  })

  it('keeps the hadith whole, links and all, when nothing marks the cut', () => {
    const plain = 'قَالَ "‏ بَيْنَا ‏"'
    expect(told(plain, null, [])).toEqual({ text: plain, names: [] })
    expect(told(arabic, null, [names[2]]).text).toBe(arabic)
  })

  it('uses the cut the server sent where there is one', () => {
    const text = 'حَدَّثَنَا زَيْدٌ عَنْ عَمْرٍو قَالَ "‏ صَلُّوا ‏"'
    const out = told(text, [text.indexOf('عَنْ'), text.indexOf('قَالَ')], [])
    expect(out.text.startsWith('عَنْ عَمْرٍو')).toBe(true)
  })
})

describe('drawnChain', () => {
  it('links each drawn name by where it stands, so a longer unlinked name never borrows a shorter one', () => {
    const arabic = 'حَدَّثَنَا عَبْدُ اللَّهِ، قَالَ حَدَّثَنَا عَبْدُ اللَّهِ بْنُ مَسْعُودٍ، قَالَ "‏ صَلُّوا ‏"'
    const first = arabic.indexOf('عَبْدُ اللَّهِ')
    const out = drawnChain(arabic, [0, arabic.lastIndexOf('قَالَ')], [[first, first + 'عَبْدُ اللَّهِ'.length, 5]])
    expect(out.main.map((l) => l.id)).toEqual([5, null])
  })

  it('hangs a weak note on the narrator whose name starts where the note says', () => {
    const arabic = 'حَدَّثَنَا زَيْدٌ، عَنْ عَمْرٍو، قَالَ "‏ صَلُّوا ‏"'
    const at = (s) => arabic.indexOf(s)
    const names = [[at('زَيْدٌ'), at('زَيْدٌ') + 6, 1], [at('عَمْرٍو'), at('عَمْرٍو') + 6, 2]]
    const out = drawnChain(arabic, [0, arabic.lastIndexOf('قَالَ')], names, [{ at: at('عَمْرٍو'), id: 2, level: 8 }])
    expect(out.main.map((l) => l.members[0].note?.level ?? null)).toEqual([null, 8])
  })
})
