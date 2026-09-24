import { describe, expect, it } from 'vitest'
import { measure, rows, share, splitConnectors } from './tarkeebLayout'

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

describe('share', () => {
  it('gives a group as many columns as it covers', () => {
    const tree = measure(AYAH)
    expect(tree.children.map(share)).toEqual([1, 1, 2])
  })

  it('gives a piece inside one word a single column', () => {
    expect(share({ role: 'حَرْفُ جَرٍّ' })).toBe(1)
  })
})

describe('splitConnectors', () => {
  // ثُمَّ فَسَوَّىٰهُنَّ سَبْعَ, shaped exactly as the API sends it: ثُمَّ (word 0)
  // already named itself with no parts at all; فَسَوَّىٰهُنَّ (word 1) glues a
  // فَ onto a verb that also takes a suffix, so its parts run three deep.
  const CONNECTOR = {
    role: 'حَرْفُ عَطْفٍ', tone: 'ghair_aamil', detail: 'joins to what came before', ghair_aamil: true,
  }
  const TREE = {
    label: 'جُمْلَةٌ فِعْلِيَّةٌ', tone: 'fil', parts: [],
    children: [
      { word: 0, role: 'حَرْفُ عَطْفٍ', tone: 'ghair_aamil', ghair_aamil: true, parts: [], children: [] },
      {
        word: 1, role: 'فِعْلٌ', tone: 'fil', prefix_arabic: 'فَ', children: [],
        parts: [CONNECTOR, { role: 'فِعْلٌ', tone: 'fil' }, { role: 'مَفْعُوْلٌ بِهِ', tone: 'mafool' }],
      },
      { word: 2, role: 'مَفْعُوْلٌ بِهِ', tone: 'mafool', children: [], parts: [] },
    ],
  }
  const WORDS = ['ثُمَّ', 'فَسَوَّىٰهُنَّ', 'سَبْعَ']

  it('leaves the tree and words untouched when nothing is glued on', () => {
    const bare = { ...TREE, children: [TREE.children[0], TREE.children[2]] }
    const result = splitConnectors(['ثُمَّ', 'سَبْعَ'], bare)
    expect(result.words).toEqual(['ثُمَّ', 'سَبْعَ'])
    expect(result.tree).toBe(bare)
    expect(result.terms).toEqual([])
  })

  it('slices the connector into its own word column, in front of the rest', () => {
    const { words } = splitConnectors(WORDS, TREE)
    expect(words).toEqual(['ثُمَّ', 'فَ', 'سَوَّىٰهُنَّ', 'سَبْعَ'])
  })

  it('renumbers every word after the split, including the ones already fine', () => {
    const { tree } = splitConnectors(WORDS, TREE)
    expect(tree.children.map((c) => c.word)).toEqual([0, 1, 2, 3])
  })

  it('keeps the rest of a compound word intact once the connector is pulled out', () => {
    const { tree } = splitConnectors(WORDS, TREE)
    const [, connector, remainder] = tree.children
    expect(connector).toMatchObject({ word: 1, role: 'حَرْفُ عَطْفٍ', tone: 'ghair_aamil', ghair_aamil: true })
    expect(remainder.word).toBe(2)
    expect(remainder.parts.map((p) => p.role)).toEqual(['فِعْلٌ', 'مَفْعُوْلٌ بِهِ'])
    expect(remainder.prefix_arabic).toBeUndefined()
  })

  it('collapses to a plain role when nothing but the connector was attached', () => {
    const lone = {
      ...TREE,
      children: [{
        word: 0, role: 'فِعْلٌ', tone: 'fil', prefix_arabic: 'وَ', children: [],
        parts: [{ ...CONNECTOR, role: 'حَرْفُ اسْتِئْنَافٍ' }, { role: 'فِعْلٌ', tone: 'fil' }],
      }],
    }
    const { tree } = splitConnectors(['وَقَامَ'], lone)
    const [, remainder] = tree.children
    expect(remainder).toMatchObject({ word: 1, role: 'فِعْلٌ', tone: 'fil', parts: [] })
  })

  it('names the toggle by the connective terms actually present', () => {
    const { terms } = splitConnectors(WORDS, TREE)
    expect(terms).toEqual(['حَرْفُ عَطْفٍ'])
  })
})
