import { describe, expect, it } from 'vitest'

import { fromAnalyzeResponse, fromAyahStore, toAnalysis, wordKey } from './analysis'

const EMPTY = { sentence: '', words: [], tree: null, summary: null, source: null, unvowelled: null }
const KEYS = Object.keys(EMPTY).sort()

describe('toAnalysis', () => {
  it('gives every field its empty value when nothing is passed', () => {
    expect(toAnalysis()).toEqual(EMPTY)
    expect(toAnalysis({ words: 'not a list' }).words).toEqual([])
  })
})

describe('fromAnalyzeResponse', () => {
  it('fills missing fields and keeps the ones sent', () => {
    expect(fromAnalyzeResponse(null)).toEqual(EMPTY)
    expect(fromAnalyzeResponse({ sentence: 'ذهب', words: [] })).toEqual({ ...EMPTY, sentence: 'ذهب' })
    const tree = { words: ['ذهب'], tree: { label: 'x' } }
    const words = [{ word: 'ذهب' }]
    const a = fromAnalyzeResponse({ sentence: 'ذهب', words, tree, summary: 'جملة فعلية', source: { key: 'nahw' }, unvowelled: { ar: 'a', en: 'b' }, parse: {}, read_failed: false })
    expect(a.words).toBe(words)
    expect(a.tree).toBe(tree)
    expect(a.summary).toBe('جملة فعلية')
    expect(Object.keys(a).sort()).toEqual(KEYS)
  })
})

describe('fromAyahStore', () => {
  it('fills missing fields, with neither request back yet', () => {
    expect(fromAyahStore()).toEqual(EMPTY)
    expect(fromAyahStore({ ayah: { words: [] } })).toEqual(EMPTY)
  })

  it('reads the words, the joined line, the corpus source and the chart', () => {
    const tarkeeb = { words: ['بِسْمِ'], tree: {}, source: { key: 'treebank' } }
    const a = fromAyahStore({ ayah: { arabic_text: 'other', words: [{ arabic: 'بِسْمِ', position: 1 }, { arabic: 'اللَّهِ', position: 2 }], source: { key: 'corpus' } }, tarkeeb })
    expect(a.sentence).toBe('بِسْمِ اللَّهِ')
    expect(a.source).toEqual({ key: 'corpus' })
    expect(a.tree).toBe(tarkeeb)
    expect(a.summary).toBeNull()
    expect(fromAyahStore({ ayah: { arabic_text: 'نص' } }).sentence).toBe('نص')
  })

  it('gives the same shape as /analyze for an equivalent sentence', () => {
    const tree = { words: ['ذَهَبَ'], tree: {} }
    const source = { key: 'x' }
    const fromAnalyze = fromAnalyzeResponse({ sentence: 'ذَهَبَ', words: [{ arabic: 'ذَهَبَ' }], tree, source })
    const fromAyah = fromAyahStore({ ayah: { words: [{ arabic: 'ذَهَبَ' }], source }, tarkeeb: tree })
    expect(fromAyah).toEqual(fromAnalyze)
    expect(Object.keys(fromAyah).sort()).toEqual(KEYS)
  })
})

describe('wordKey', () => {
  it('is the position, else the index', () => {
    expect(wordKey({ position: 3 }, 0)).toBe(3)
    expect(wordKey({}, 2)).toBe(2)
  })
})
