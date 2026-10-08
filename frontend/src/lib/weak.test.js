import { describe, expect, it } from 'vitest'

import { weakLinks, weakPoints } from './weak'

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

const rules = {
  kinds: { tadlis: { label: 'Possible tadlis', say: 'no hearing', quote: 'q1', source: 'Salah', page: 'p. 2' }, not_heard: { label: 'Possible break', say: 'did not hear' } },
  levels: { 3: { say: 'level three', quote: 'q3', source: 'Tarif', page: 'p. 1' } },
}
const person = (id, name, ...ties) => ({ id, name, note: null, ties })
const tie = (at, student, teacher, kind = 'tadlis', extra = {}) => ({ at, student, teacher, kind, sub: '', word: 'عن', level: 3, quote: '', source: '', page: '', ...extra })

describe('weakLinks', () => {
  it('lists links from the top of the drawing, lettered, and never ranks them with narrators', () => {
    const main = [person(1, 'a'), person(2, 'b', tie(10, 1, 2)), person(3, 'c', tie(20, 2, 3, 'not_heard', { sub: 'not_heard', quote: 'ql', scholar: 'x', source: 'Jami', page: 'no. 4' }))]
    const out = weakLinks({ main, branches: [] }, { ...rules, kinds: { ...rules.kinds, not_heard: { label: 'Possible break', say: 'did not hear' } } })
    expect(out.map((p) => [p.letter, p.teller, p.teacherName, p.label])).toEqual([['a', 'b', 'c', 'Possible break'], ['b', 'a', 'b', 'Possible tadlis']])
    expect(out[1].quotes.map((q) => q.quote)).toEqual(['q3', 'q1'])   // the teller's level, the link's wording
    expect(out[0].quotes).toEqual([{ quote: 'ql', source: 'Jami', page: 'no. 4' }])
  })

  it('leaves out a link whose teller is not drawn, one with no rule, and counts a pair once', () => {
    const main = [person(2, 'b', tie(10, 9, 2), tie(11, 1, 2, 'mystery')), person(1, 'a'), person(3, 'c', tie(20, 1, 3), tie(21, 1, 3))]
    expect(weakLinks({ main, branches: [] }, rules).map((p) => p.teacher)).toEqual([3])
    expect(weakLinks({ main, branches: [] }, null)).toEqual([])
  })
})
