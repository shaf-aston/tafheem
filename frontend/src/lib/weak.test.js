import { describe, expect, it } from 'vitest'

import { weakPoints } from './weak'

const scale = [5, 6, 8, 11].map((level) => ({
  level, en: `level ${level}`, source: 'Taqrib', lift: level === 5 ? { memory: { en: 'lifted' } } : {},
}))
const link = (name, note) => ({ name, id: note ? note.at : null, note: note ?? null })
const note = (at, level, kind = 'weak') => ({ at, id: at, level, kind, grade: 'g' })
const chain = (...main) => ({ main, branches: [] })

describe('weakPoints', () => {
  it('ranks weakest first and gives equal levels one rank, printed with an equals sign', () => {
    const out = weakPoints(chain(link('a', note(1, 8)), link('b', note(2, 11)), link('c', note(3, 8)), link('d', note(4, 6))), scale)
    expect(out.map((p) => [p.name, p.label])).toEqual([['b', '1'], ['a', '2='], ['c', '2='], ['d', '4']])
  })

  it('is empty for a chain with no notes, and for notes the scale does not know', () => {
    expect(weakPoints(chain(link('a', null)), scale)).toEqual([])
    expect(weakPoints(chain(link('a', note(1, 9))), scale)).toEqual([])
    expect(weakPoints(chain(link('a', note(1, 8))), [])).toEqual([])
  })

  it('counts a narrator once where two strands both name him', () => {
    const out = weakPoints({ main: [link('a', note(1, 8))], branches: [{ links: [link('a', { ...note(9, 8), id: 1 })], join: null }] }, scale)
    expect(out.map((p) => p.label)).toEqual(['1'])
  })

  it('counts a narrator once where a branch joins the main strand, and finds weak ones on a branch', () => {
    const joined = link('a', note(1, 8))
    const out = weakPoints({ main: [joined], branches: [{ links: [link('b', note(2, 5, 'memory'))], join: { ...joined } }] }, scale)
    expect(out.map((p) => p.name)).toEqual(['a', 'b'])
    expect(out[1].lift).toEqual({ en: 'lifted' })
    expect(out[0].lift).toBeNull()
  })
})
