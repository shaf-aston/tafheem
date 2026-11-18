import { describe, expect, it } from 'vitest'

import settings from '../../config/colloquial-display.json'
import { grouped } from './wordGroups'

const MIN = settings['least-under-heading']
const run = (category, n) => Array.from({ length: n }, (_, i) => ({ id: `${category ?? 'none'}-${i}`, category }))

describe('grouped', () => {
  it('heads a list by its categories when every one is big enough, in the order written', () => {
    const rows = [...run('a', MIN), ...run('b', MIN + 3)]
    expect(grouped(rows).map(([heading, words]) => [heading, words.length])).toEqual([['a', MIN], ['b', MIN + 3]])
  })

  it('one category too small, and the whole list is one plain run: no heading over two or three words', () => {
    const rows = [...run('family', 3), ...run('furniture', 20)]
    const out = grouped(rows)
    expect(out).toHaveLength(1)
    expect(out[0][0]).toBe('')
    expect(out[0][1]).toEqual(rows)   // nothing lost, nothing reordered
  })

  it('a single category needs no heading', () => {
    expect(grouped(run('a', MIN * 2)).map(([heading]) => heading)).toEqual([''])
  })

  it('words with no category sit under no heading, and no words is no run', () => {
    expect(grouped(run(undefined, 2))).toEqual([['', run(undefined, 2)]])
    expect(grouped([])).toEqual([])
  })
})
