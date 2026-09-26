import { describe, expect, it } from 'vitest'

import config from '../colloquial.json'
import schema from './unit.schema.json'
import { checkLesson, checkSchema, formatReport, validateAll } from './validate'

// Structure-only fixtures: placeholder strings, no Arabic authored here.
const MIN = config['lesson-minimums']
const TYPES = Object.keys(config['exercise-types'])
const times = (n, make) => Array.from({ length: n }, (_, i) => make(i))
const exercise = (i, over = {}) => ({
  id: `e${i}`, type: 'say_it', prompt: 'p', answer: 'a', accepted: ['a'], too_formal: [], tip: 't', ...over,
})
const lesson = (id, over = {}) => ({
  id, situation: 's', goal: 'g',
  phrases: times(MIN.phrases, () => ({ ar: 'x', translit: 'x', en: 'x', use: 'x', reply: null })),
  dialogue: times(MIN.dialogue, () => ({ speaker: 'A', ar: 'x', translit: 'x', en: 'x' })),
  de_book: times(MIN.de_book, () => ({ book: 'x', natural: 'x', why: 'x' })),
  grammar: null, culture: 'c',
  exercises: times(MIN.exercises, (i) => exercise(i)),
  ...over,
})
const unit = (lessons) => ({
  unit: 'unit-01', title: 'T', lessons,
  challenge: { scenario: 's', partner_role: 'r', learner_goals: [], target_phrases: [], checklist: [] },
})
const withExercise = (ex) => lesson('1.1', { exercises: [ex, ...times(MIN.exercises - 1, (i) => exercise(i + 1))] })

describe('unit validator', () => {
  it('passes a well-formed unit', () => {
    expect(validateAll({ 'unit-01.json': unit([lesson('1.1')]) })).toEqual([])
  })

  it('keeps the schema type list and colloquial.json in step', () => {
    const e = schema.properties.lessons.items.properties.exercises.items.properties.type.enum
    expect(e).toEqual(TYPES)
  })

  it('reports shape problems with their path, and never renames keys', () => {
    const u = unit([lesson('1.1', { cultur: 'c' })])
    delete u.lessons[0].culture
    const problems = checkSchema(u).map((p) => `${p.path}: ${p.problem}`)
    expect(problems).toEqual(['lessons[0].culture: missing', 'lessons[0].cultur: unexpected key'])
  })

  it('rejects an unknown exercise type', () => {
    const u = unit([withExercise(exercise(0, { type: 'dictation' }))])
    expect(validateAll({ f: u })[0].problem).toMatch(/not one of/)
  })

  it('reports lists below the minimum', () => {
    expect(checkLesson(lesson('1.1', { de_book: [] }))).toEqual([`de_book: 0, needs at least ${MIN.de_book}`])
  })

  it('allows options only on listen_choose and given_lines only on respond/role_play', () => {
    expect(checkLesson(withExercise(exercise(0, { options: ['a'] })))[0]).toMatch(/options is only for listen_choose/)
    expect(checkLesson(withExercise(exercise(0, { type: 'listen_choose' })))[0]).toMatch(/needs options/)
    expect(checkLesson(withExercise(exercise(0, { given_lines: ['a'] })))[0]).toMatch(/given_lines is only for respond, role_play/)
    expect(checkLesson(withExercise(exercise(0, { type: 'respond', given_lines: ['a'] })))).toEqual([])
  })

  it('needs answer, tip and one accepted form', () => {
    expect(checkLesson(withExercise(exercise(0, { answer: ' ', tip: '', accepted: [] })))).toEqual([
      'exercise e0: answer is empty', 'exercise e0: tip is empty', 'exercise e0: accepted needs at least one form',
    ])
  })

  it('flags a form that is both accepted and too formal once normalised', () => {
    // The same letter with and without a fatha: only the normaliser makes them equal.
    const ex = exercise(0, { accepted: ['ه'], too_formal: [{ answer: 'هَ', feedback: 'f' }] })
    expect(checkLesson(withExercise(ex))).toEqual(['exercise e0: "هَ" is both accepted and too_formal'])
  })

  it('flags lesson ids used twice across units', () => {
    const problems = validateAll({ 'unit-01.json': unit([lesson('1.1')]), 'unit-02.json': unit([lesson('1.1')]) })
    expect(problems).toEqual([{ file: 'unit-02.json', lesson: '1.1', problem: 'lesson id also used in unit-01.json' }])
  })

  it('formats file → lesson → problem', () => {
    expect(formatReport([{ file: 'a.json', lesson: '1.1', problem: 'x' }], 1)).toBe(
      '1 unit file(s), 1 problem(s)\n\na.json\n  1.1\n    - x',
    )
  })
})
