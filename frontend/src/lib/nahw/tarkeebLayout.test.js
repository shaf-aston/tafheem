import { describe, expect, it } from 'vitest'
import { align, cells, fold, foldRows, groupThreads, hiddenWords, layout, measure, rows, textOf, threadSpans, tones } from './tarkeebLayout'

/** Shaped exactly as the API sends it: empty arrays, not missing keys. */
const AYAH = {
  label: 'جُمْلَةٌ اِسْمِيَّةٌ',
  children: [
    { word: 0, role: 'مُبْتَدَأٌ', children: [], parts: [] },
    { word: 1, role: 'خَبَرٌ', children: [], parts: [{ role: 'حَرْفُ جَرٍّ' }, { role: 'مَجْرُوْرٌ' }] },
    {
      label: 'مُرَكَّبٌ إِضَافِيٌّ',
      role: '؟ لَمْ يُحَلَّلْ',
      gap: true,
      parts: [],
      children: [
        { word: 2, role: 'مُضَافٌ', children: [], parts: [] },
        { word: 3, role: 'مُضَافٌ إِلَيْهِ', children: [], parts: [] },
      ],
    },
  ],
  parts: [],
}

describe('measure', () => {
  it('gives every group the span of the words underneath it', () => {
    const tree = measure(AYAH)
    expect([tree.from, tree.to]).toEqual([0, 3])
    expect(tree.children.map((c) => [c.from, c.to])).toEqual([[0, 0], [1, 1], [2, 3]])
  })

  it('counts a word with pieces inside it as one join deep', () => {
    const [plain, withParts] = measure(AYAH).children
    expect(plain.level).toBe(0)
    expect(withParts.level).toBe(1)
  })

  it('leaves the tree it was given untouched', () => {
    measure(AYAH)
    expect(AYAH.children[0].from).toBeUndefined()
  })

  it('reads an empty array as no children, which is what the API sends', () => {
    expect(measure({ word: 0, children: [], parts: [] }).level).toBe(0)
  })
})

describe('rows', () => {
  const laid = rows(AYAH, 4)

  it('draws one row per level of joining', () => {
    expect(laid.map((r) => r.level)).toEqual([1, 2])
  })

  it('puts each group on the row where its join happens', () => {
    expect(laid[0].groups.map((g) => [g.from, g.to])).toEqual([[1, 1], [2, 3]])
    expect(laid[1].groups.map((g) => [g.from, g.to])).toEqual([[0, 3]])
  })

  it('runs a thread down from a word whose role is not written yet', () => {
    // الْحَمْدُ is only named at the top, so it threads through the row below it.
    expect(laid[0].threads).toEqual([0])
    expect(laid[1].threads).toEqual([])
  })
})

describe('foldRows', () => {
  const levels = [1, 2, 3, 4, 5, 6].map((level) => ({ level, groups: [], threads: [] }))

  it('keeps the rows nearest the words and counts the rest', () => {
    const { shown, more } = foldRows(levels, 4)
    expect(shown.map(({ level }) => level)).toEqual([1, 2, 3, 4])
    expect(more).toBe(2)
  })

  it('folds nothing from a chart that already fits', () => {
    expect(foldRows(levels.slice(0, 3), 4)).toEqual({ shown: levels.slice(0, 3), more: 0 })
  })

  it('shows every row when asked to keep them all', () => {
    expect(foldRows(levels, Infinity)).toEqual({ shown: levels, more: 0 })
  })
})

describe('threadSpans', () => {
  it('draws a thread passing several rows as one line from the word to its name', () => {
    const levels = [
      { level: 1, threads: [0, 2] },
      { level: 2, threads: [0] },
      { level: 3, threads: [0, 2] },
    ]
    // word 2 is not threaded on level 2 (a group covers it there), so its two stretches are two lines
    expect(threadSpans(levels)).toEqual([
      { word: 0, from: 1, to: 3 },
      { word: 2, from: 1, to: 1 },
      { word: 2, from: 3, to: 3 },
    ])
  })
})

describe('a word named as its first piece', () => {
  // لْـ يَصُمْهُ: the verb's pieces are written in its sentence's row, فعل once
  const CLAUSE = {
    label: 'جُمْلَةٌ فِعْلِيَّةٌ',
    children: [
      { word: 0, role: 'لام الأمر', children: [], parts: [] },
      { word: 1, role: 'فعل', children: [], parts: [{ role: 'فعل' }, { role: 'فاعل' }, { role: 'مفعول به' }] },
    ],
  }

  it('adds no row of its own', () => {
    expect(rows(CLAUSE, 2).map((r) => r.level)).toEqual([1])
  })

  it('writes its pieces in its parent row, the word itself once', () => {
    expect(cells(measure(CLAUSE)).map((c) => [c.from, c.roles.map((r) => r.role)])).toEqual([
      [0, ['لام الأمر']], [1, ['فعل', 'فاعل', 'مفعول به']]])
  })

  it('keeps the row of a word whose pieces make another job', () => {
    expect(measure(AYAH).children[1].level).toBe(1)
  })
})

describe('cells', () => {
  it('puts each name over the columns of its own words', () => {
    expect(cells(measure(AYAH)).map((c) => [c.from, c.to])).toEqual([[0, 0], [1, 1], [2, 3]])
  })

  it('puts the pieces of a word over that word', () => {
    const word = measure(AYAH).children[1]
    expect(cells(word)).toEqual([{ from: 1, to: 1, roles: word.parts }])
  })
})

describe('fold, the Merged view', () => {
  // فَلْيَصُمْهُ زَيْدٌ as the API sends it: one written word cut into three columns
  const CUT = {
    words: ['فَ', 'لْ', 'يَصُمْهُ', 'زَيْدٌ'],
    written: [0, 0, 0, 1],
    tree: {
      label: 'جملة',
      children: [
        { word: 0, role: 'حرف رابط', tone: 'harf' },
        {
          label: 'جواب الشرط', role: 'جواب الشرط',
          children: [
            { word: 1, role: 'لام الأمر', tone: 'harf' },
            { word: 2, role: 'فعل', tone: 'fil', parts: [{ role: 'فعل' }, { role: 'فاعل' }] },
            { word: 3, role: 'فاعل', tone: 'fail' },
          ],
        },
      ],
    },
  }
  const merged = fold(CUT)

  it('puts each written word back in one column', () => {
    expect(merged.words).toEqual(['فَلْيَصُمْهُ', 'زَيْدٌ'])
  })

  it('reads the pieces sharing a column as one cell, in order', () => {
    const answer = measure(merged.tree).children[1]
    expect(cells(answer).map((c) => [c.from, c.to, c.roles.map((r) => r.role)])).toEqual([
      [0, 0, ['لام الأمر', 'فعل', 'فاعل']], [1, 1, ['فاعل']]])
    expect(cells(measure(merged.tree)).map((c) => c.roles.map((r) => r.role))).toEqual([['حرف رابط', 'جواب الشرط']])
  })

  it('changes nothing when no word was cut', () => {
    const whole = fold({ words: ['زَيْدٌ', 'قَامَ'], tree: { children: [{ word: 0, role: 'فاعل' }, { word: 1, role: 'فعل' }] } })
    expect(whole.words).toEqual(['زَيْدٌ', 'قَامَ'])
  })
})

describe('cells and tones', () => {
  it('writes no name, and no "+", for a group named only by its own brace', () => {
    const tree = measure({ children: [
      { word: 0, role: 'حرف' },
      { label: 'متعلق', children: [{ word: 1, role: 'حرف جر' }, { word: 2, role: 'مجرور' }] },
      { word: 3, role: 'فعل' },
    ] })
    expect(cells(tree).map((c) => c.roles.map((r) => r.role))).toEqual([['حرف'], ['فعل']])
  })

  it('gives each column the tone of the word drawn in it, open ones as gaps', () => {
    expect(tones({ children: [{ word: 0, tone: 'fil' }, { word: 1, gap: true, tone: 'fil' }] })).toEqual(['fil', 'gap'])
  })
})

describe('hiddenWords', () => {
  it('finds the leaves marked understood, wherever they sit', () => {
    const tree = {
      label: 'x',
      children: [
        { word: 0, role: 'a', children: [], parts: [] },
        { label: 'y', children: [{ word: 1, role: 'b', hidden: true, children: [], parts: [] }], parts: [] },
      ],
      parts: [],
    }
    expect([...hiddenWords(tree)]).toEqual([1])
  })
})

describe('groupThreads', () => {
  // يَا أَيُّهَا النَّاسُ اعْبُدُوا رَبَّكُمْ: رَبَّ+كُمْ is a مركب إضافي on row 1 whose job, مفعول به,
  // is written on the sentence's row 3 (the نداء unit beside it is two rows tall)
  const leaf = (word, role) => ({ word, role, children: [], parts: [] })
  const tree = {
    label: 'جملة فعلية',
    children: [
      { label: 'جملة ندائية', children: [leaf(0, 'حرف نداء'), { label: 'مركب توصيفي', role: 'منادى', children: [leaf(1, 'موصوف'), leaf(2, 'صفة')] }] },
      leaf(3, 'فعل'),
      { label: 'مركب إضافي', role: 'مفعول به', children: [leaf(4, 'مضاف'), leaf(5, 'مضاف إليه')] },
    ],
  }

  it('threads a unit from its own row down to the row its job is written on', () => {
    expect(groupThreads(rows(tree, 6))).toEqual([{ from: 4, to: 5, rowFrom: 2, rowTo: 2 }])
  })

  it('threads nothing past the rows shown', () => {
    expect(groupThreads(foldRows(rows(tree, 6), 2).shown)).toEqual([])
  })

  it('does not thread a unit with no job to reach', () => {
    const plain = { label: 'جملة', children: [{ label: 'x', children: [leaf(0, 'a'), leaf(1, 'b')] }, { label: 'y', children: [{ label: 'z', children: [leaf(2, 'c'), leaf(3, 'd')] }, leaf(4, 'e')] }] }
    expect(groupThreads(rows(plain, 5))).toEqual([])
  })
})

// فَـ + سَوَّىٰهُنَّ cut into two columns of one written word, then an understood
// (ثابت) column, then a plain word: the shapes a tapped word has to survive.
const CUT = {
  words: ['فَ', 'سَوَّىٰهُنَّ', '(ثابت)', 'زَيْدٌ'],
  written: [0, 0, -1, 1],
  tree: {
    label: 'جُمْلَةٌ',
    parts: [],
    children: [
      { word: 0, role: 'حَرْفُ عَطْفٍ', tone: 'harf', children: [], parts: [] },
      { word: 1, role: 'فِعْلٌ', tone: 'verb', children: [], parts: [] },
      { word: 2, role: 'خَبَرٌ', tone: 'khabar', hidden: true, children: [], parts: [] },
      { word: 3, role: 'فَاعِلٌ', tone: 'fail', children: [], parts: [] },
    ],
  },
}

describe('textOf', () => {
  it('joins the pieces of one written word and spaces written words', () => {
    expect(textOf(CUT, [0, 1, 3])).toBe('فَسَوَّىٰهُنَّ زَيْدٌ')
  })

  it('copies a word typed with a tatweel as it was typed', () => {
    expect(textOf({ words: ['اللـه'] }, [0])).toBe('اللـه')
  })

  it('spaces every column when nothing says which word it was cut from', () => {
    expect(textOf({ words: ['أ', 'ب'] }, [0, 1])).toBe('أ ب')
  })
})

describe('layout', () => {
  it('gives one entry per written word, its pieces in their own colours and its place on the page', () => {
    const { written } = layout(CUT)
    expect(written.map((w) => [w.from, w.to, w.text, w.hidden, w.nth])).toEqual([
      [0, 1, 'فَسَوَّىٰهُنَّ', false, 0],
      [2, 2, '(ثابت)', true, null],
      [3, 3, 'زَيْدٌ', false, 1],
    ])
    expect(written[0].pieces).toEqual([{ text: 'فَ', tone: 'harf' }, { text: 'سَوَّىٰهُنَّ', tone: 'verb' }])
  })

  it('hands a tap the word without the tatweel a book\'s example cuts with (فَـ)', () => {
    expect(layout({ ...CUT, words: ['فَـ', ...CUT.words.slice(1)] }).written[0].text).toBe('فَسَوَّىٰهُنَّ')
  })

  it('merged, draws each written word in one column, and counts the page the same way', () => {
    const merged = layout(CUT, { mode: 'merged' })
    expect(merged.words).toHaveLength(3)
    expect(merged.written.map((w) => w.nth)).toEqual(layout(CUT).written.map((w) => w.nth))
  })

  it('holds back the rows past `keep`, and says how many', () => {
    const deep = (word, last) => (word === last
      ? { word, role: 'خَبَرٌ', children: [], parts: [] }
      : { label: 'جُمْلَةٌ', children: [{ word, role: 'مُبْتَدَأٌ', children: [], parts: [] }, deep(word + 1, last)], parts: [] })
    const tarkeeb = { words: ['أ', 'ب', 'ت', 'ث'], tree: deep(0, 3) }
    expect(layout(tarkeeb).levels).toHaveLength(3)
    const folded = layout(tarkeeb, { keep: 2 })
    expect([folded.levels.length, folded.more]).toEqual([2, 1])
    expect(folded.threads.every((t) => t.to <= 2)).toBe(true)
  })
})

describe('align', () => {
  const page = (...texts) => texts.map((text, nth) => ({ text, hidden: false, nth }))
  const listed = (key, ...texts) => texts.map((text, at) => ({ [key]: text, at }))
  const ats = (found) => found.map((item) => item?.at)

  it('by place, takes the nth card for the nth word when the counts agree, whatever the spelling', () => {
    // an ayah's record writes ٱلرَّحْمَٰنِ where الرحمن was typed: still that card
    const cards = listed('word', 'بسم', 'الله', 'الرحمن')
    expect(ats(align(page('بِسْمِ', 'ٱللَّهِ', 'ٱلرَّحْمَٰنِ'), cards, 'word', { byPlace: true }))).toEqual([0, 1, 2])
  })

  it('leaves an understood word out: it has no card', () => {
    const written = [...page('قَامَ'), { text: '(ثابت)', hidden: true, nth: null }, { text: 'زَيْدٌ', hidden: false, nth: 1 }]
    expect(ats(align(written, listed('word', 'قام', 'زيد'), 'word', { byPlace: true }))).toEqual([0, 1])
  })

  it('never trusts the English list by place: as long as the page by chance, each word still needs its own letters', () => {
    const glosses = listed('arabic', 'في البيت', 'رجل', 'و', 'قال')
    expect(ats(align(page('في', 'البيت', 'رجل', 'وقال'), glosses, 'arabic'))).toEqual([undefined, undefined, 1, undefined])
  })

  it('keeps the order of both, so a word said twice gets its own item, not the next one\'s', () => {
    // the English list dropped the first قال: the second keeps its own
    expect(ats(align(page('قال', 'زيد', 'قال'), listed('arabic', 'زيد', 'قال'), 'arabic'))).toEqual([undefined, 0, 1])
    // counts apart, a repeated word nearer its own place
    const cards = listed('word', 'زيد', 'قال', 'إن', 'زيد', 'قائم')
    expect(ats(align(page('قال', 'إن', 'زيد'), cards, 'word', { byPlace: true }))).toEqual([1, 2, 3])
  })

  it('never gives one item to two words', () => {
    expect(ats(align(page('زيد', 'زيد'), listed('word', 'زيد', 'هو', 'قائم'), 'word'))).toEqual([0, undefined])
  })

  it('finds nothing for a word with no item of its letters, and nothing at all from no list', () => {
    expect(ats(align(page('قال', 'عمرو'), listed('word', 'قال', 'زيد', 'هو'), 'word'))).toEqual([0, undefined])
    expect(align(page('قال'), undefined, 'arabic')).toEqual([undefined])
  })

  it('matches no word to an item with no Arabic, even one whose letters come to nothing', () => {
    expect(ats(align(page('َ', 'قال'), [{ at: 0 }, ...listed('arabic', 'قال').map((g) => ({ ...g, at: 1 }))], 'arabic'))).toEqual([undefined, 1])
  })
})
