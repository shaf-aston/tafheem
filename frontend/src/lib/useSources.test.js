import { describe, expect, it } from 'vitest'

import { sourcesFor } from './useSources'

const CORPUS = { key: 'corpus', used_in: ['quran', 'quiz'] }
const RULES = { key: 'rules', used_in: ['sarf'] }
const ORPHAN = { key: 'orphan' } // no used_in at all, an unfinished entry
const NOWHERE = { key: 'nowhere', used_in: [] }

describe('sourcesFor', () => {
  it('gives a tab only the sources that name it', () => {
    expect(sourcesFor([CORPUS, RULES], 'sarf')).toEqual([RULES])
  })

  it('gives a source to every tab it names, not just the first', () => {
    expect(sourcesFor([CORPUS], 'quran')).toEqual([CORPUS])
    expect(sourcesFor([CORPUS], 'quiz')).toEqual([CORPUS])
  })

  it('keeps the order the backend sent, so the footer reads like the file', () => {
    expect(sourcesFor([CORPUS, RULES, { key: 'ai', used_in: ['sarf'] }], 'sarf'))
      .toEqual([RULES, { key: 'ai', used_in: ['sarf'] }])
  })

  it('returns nothing for a tab no source names, rather than everything', () => {
    // The footer turns this into "No sources are declared for this tab." A
    // filter that fell back to the whole list would credit a tab with sources
    // it does not read, which is the one thing this line must never do.
    expect(sourcesFor([CORPUS, RULES], 'dict')).toEqual([])
  })

  it('ignores a source with no used_in instead of throwing', () => {
    // An entry half-added to sources.json must not take down the page footer.
    expect(sourcesFor([ORPHAN, NOWHERE, RULES], 'sarf')).toEqual([RULES])
  })

  it('survives an empty list', () => {
    expect(sourcesFor([], 'quran')).toEqual([])
  })
})
