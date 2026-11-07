import { describe, expect, it } from 'vitest'

import settings from '../../config/colloquial-display.json'
import { grouped } from './wordGroups'

const MIN = settings['least-under-heading']
const run = (category, n) => Array.from({ length: n }, (_, i) => ({ id: `${category ?? 'none'}-${i}`, category }))

describe('grouped', () => {
  it('keeps the order written, each category once, under its own heading', () => {
    const rows = [...run('a', MIN), ...run('b', MIN)]
    expect(grouped(rows).map(([heading, words]) => [heading, words.length])).toEqual([['a', MIN], ['b', MIN]])
  })

  it('a category too small for a heading joins the heading before it', () => {
    const rows = [...run('a', MIN), ...run('tiny', MIN - 1)]
    const out = grouped(rows)
    expect(out.map(([heading]) => heading)).toEqual(['a'])
    expect(out[0][1]).toHaveLength(MIN + MIN - 1)
  })

  it('a small category with nothing before it still has its own heading', () => {
    expect(grouped(run('tiny', MIN - 1)).map(([heading]) => heading)).toEqual(['tiny'])
  })

  it('words with no category sit under no heading', () => {
    expect(grouped(run(undefined, 2))).toEqual([['', run(undefined, 2)]])
    expect(grouped([])).toEqual([])
  })
})
