import { describe, expect, it } from 'vitest'

import { LEVEL_IDS, LEVELS, RULES, classify, levelOf } from './learnerLevel'

// Answers in a module: `n` given, `right` of them right.
const row = (module, n, right) => ({ module, attempts: n, correct: right, learnt: 0 })
const MIN = RULES.minAnswers

describe('levels.json', () => {
  it('runs beginner, intermediate, advanced, with proof under all but the top', () => {
    expect(LEVEL_IDS).toEqual(['beginner', 'intermediate', 'advanced'])
    expect(LEVELS.slice(0, -1).every((level) => level.proof.length > 0)).toBe(true)
    expect(LEVELS.at(-1).proof).toEqual([])
  })

  it('finds a level by id, and nothing for an unknown one', () => {
    expect(levelOf('advanced').label).toBe('Advanced')
    expect(levelOf('expert')).toBeNull()
    expect(levelOf('')).toBeNull()
  })

  it('keeps fail below pass', () => {
    expect(RULES.fail).toBeLessThan(RULES.pass)
  })
})

describe('classify', () => {
  it('gives back the choice while no tier has enough answers', () => {
    const few = [row('basics', MIN - 1, MIN - 1), row('quiz', MIN - 1, 0)]
    expect(classify('advanced', few)).toEqual({ level: 'advanced', settled: false, basis: null })
    expect(classify('', [])).toEqual({ level: '', settled: false, basis: null })
    expect(classify('beginner')).toEqual({ level: 'beginner', settled: false, basis: null })
  })

  it('counts a tier at exactly the minimum', () => {
    expect(classify('beginner', [row('basics', MIN, MIN)]).settled).toBe(true)
  })

  it('ignores modules no tier names', () => {
    expect(classify('beginner', [row('nawawi40', 500, 500)]).settled).toBe(false)
  })

  it('moves past a passed tier', () => {
    const result = classify('beginner', [row('basics', 40, 36)])
    expect(result).toEqual({ level: 'intermediate', settled: true, basis: { id: 'beginner', answers: 40, share: 0.9 } })
  })

  it('passes at exactly the pass share, and not just under it', () => {
    expect(classify('beginner', [row('basics', 50, 40)]).level).toBe('intermediate')
    expect(classify('beginner', [row('basics', 50, 39)]).level).toBe('beginner')
  })

  it('adds the tier modules together', () => {
    // 20 + 20 answers: neither alone is enough, together they are, at 85%.
    const result = classify('beginner', [row('quiz', 20, 17), row('quiz:ur', 20, 17)])
    expect(result.level).toBe('advanced')
    expect(result.basis).toEqual({ id: 'intermediate', answers: 40, share: 0.85 })
  })

  it('stops at the top level', () => {
    expect(classify('advanced', [row('quiz', 40, 40)]).level).toBe('advanced')
  })

  it('holds a tier answered well enough, short of a pass', () => {
    const result = classify('beginner', [row('quiz', 40, 28)])
    expect(result.level).toBe('intermediate')
    expect(result.basis.id).toBe('intermediate')
  })

  it('holds at exactly the fail share, and puts back just under it', () => {
    expect(classify('advanced', [row('quiz', 50, 30)]).level).toBe('advanced')
    expect(classify('advanced', [row('quiz', 50, 29)]).level).toBe('intermediate')
  })

  it('puts a learner back on the tier they struggle with', () => {
    const result = classify('advanced', [row('quiz', 40, 20)])
    expect(result).toEqual({ level: 'intermediate', settled: true, basis: { id: 'intermediate', answers: 40, share: 0.5 } })
  })

  it('caps at the lowest struggled tier even when a higher one went well', () => {
    const result = classify('intermediate', [row('basics', 30, 12), row('quiz', 40, 40)])
    expect(result.level).toBe('beginner')
    expect(result.basis.id).toBe('beginner')
  })

  it('keeps a beginner who struggles a beginner, and says why', () => {
    expect(classify('beginner', [row('basics', 30, 3)])).toEqual({
      level: 'beginner', settled: true, basis: { id: 'beginner', answers: 30, share: 0.1 },
    })
  })

  it('places someone who never chose, from their answers alone', () => {
    expect(classify('', [row('quiz', 30, 27)]).level).toBe('advanced')
    expect(classify('', [row('basics', 30, 3)]).level).toBe('beginner')
    expect(classify('', [row('quiz', 30, 21)]).level).toBe('intermediate')
  })

  it('keeps a higher choice the answers do not contradict', () => {
    const result = classify('advanced', [row('basics', 40, 40)])
    expect(result.level).toBe('advanced')
    expect(result.basis.id).toBe('beginner')
  })

  it('reads its thresholds from the rules it is given', () => {
    const rules = { ...RULES, minAnswers: 2, pass: 0.5, fail: 0.25 }
    expect(classify('beginner', [row('basics', 2, 1)], rules).level).toBe('intermediate')
    expect(classify('intermediate', [row('quiz', 4, 0)], rules).level).toBe('intermediate')
    expect(classify('advanced', [row('quiz', 4, 0)], rules).level).toBe('intermediate')
  })
})
