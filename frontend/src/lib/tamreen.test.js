import { describe, expect, it } from 'vitest'

import {
  answerParts, buildQueue, doubtsOf, gradeGrid, gradePart, gradeRule, isFullyCorrect,
  markedWords, narrowQueue, partPicks, proseParts, rowName, scoreOf, sentenceLines, statusOf,
} from './tamreen'

const rule = {
  id: 'haal-r01',
  question: 'حال can be...',
  options: ['a', 'b', 'c', 'd'],
  answer: ['a', 'c'],
  tags: ['haal'],
}

const example = {
  id: 'haal-e01',
  sentence: 'يَصُدُّونَ وَهُمْ مُسْتَكْبِرُونَ\nthey walk away arrogantly.',
  marked: [
    { text: 'وَهُمْ مُسْتَكْبِرُونَ', style: 'blue underline' },
    { text: 'يَصُدُّونَ', style: 'blue underline' },
    { text: 'هُمْ مُسْتَكْبِرُونَ', style: 'green underline' },
  ],
  parts: [
    {
      letter: 'a',
      question: 'q',
      options: ['ليست حالا', 'حال'],
      rows: ['يَصُدُّونَ', 'وَهُمْ'],
      answer: { 'يَصُدُّونَ': ['حال'], 'وَهُمْ': ['حال'] },
      by: 'teacher',
    },
    { letter: 'b', question: 'explain', answer: 'because...', by: 'teacher' },
  ],
  tags: ['haal'],
}

const exercises = [{ key: 'haal', title: 't', form: 'f', harvested: 'h', rules: [rule], examples: [example] }]

describe('buildQueue', () => {
  it('flattens rules then examples per exercise, tagging each with its exercise', () => {
    const q = buildQueue(exercises)
    expect(q).toEqual([
      { kind: 'rule', item: rule, exerciseKey: 'haal' },
      { kind: 'example', item: example, exerciseKey: 'haal' },
    ])
  })

  it('is empty for no exercises', () => {
    expect(buildQueue([])).toEqual([])
    expect(buildQueue(undefined)).toEqual([])
  })
})

describe('sentenceLines', () => {
  it('splits the Arabic line from the English gloss under it', () => {
    expect(sentenceLines(example)).toEqual({
      arabic: 'يَصُدُّونَ وَهُمْ مُسْتَكْبِرُونَ',
      gloss: 'they walk away arrogantly.',
    })
  })
})

describe('markedWords', () => {
  it('sorts marked words into blue and green, blue winning where both claim a word', () => {
    const { blue, green } = markedWords(example)
    expect(blue).toEqual(new Set(['وَهُمْ', 'مُسْتَكْبِرُونَ', 'يَصُدُّونَ']))
    // green claimed مُسْتَكْبِرُونَ too, but blue already had it
    expect(green).toEqual(new Set(['هُمْ']))
  })
})

describe('answerParts / proseParts / doubtsOf', () => {
  it('splits ticked parts from written ones', () => {
    expect(answerParts(example).map((p) => p.letter)).toEqual(['a'])
    expect(proseParts(example).map((p) => p.letter)).toEqual(['b'])
  })

  it('is empty when an example has no parts', () => {
    expect(answerParts({ parts: [] })).toEqual([])
    expect(proseParts({})).toEqual([])
  })

  it('collects the example doubt and every part doubt', () => {
    const doubtful = { doubt: 'top', parts: [{ doubt: 'part-a' }, {}] }
    expect(doubtsOf(doubtful)).toEqual(['top', 'part-a'])
    expect(doubtsOf(example)).toEqual([])
  })
})

describe('gradeRule', () => {
  it('marks picked-right as ok, picked-wrong as bad, missed-right as miss', () => {
    const { options, correct } = gradeRule(rule, new Set(['a', 'b']))
    expect(options).toEqual([
      { option: 'a', picked: true, status: 'ok' },
      { option: 'b', picked: true, status: 'bad' },
      { option: 'c', picked: false, status: 'miss' },
      { option: 'd', picked: false, status: '' },
    ])
    expect(correct).toBe(false)
  })

  it('is correct only when picks exactly match the answer set', () => {
    expect(gradeRule(rule, new Set(['a', 'c'])).correct).toBe(true)
  })
})

describe('gradeGrid', () => {
  const part = example.parts[0]

  it('grades every row independently', () => {
    const picks = { 'يَصُدُّونَ': ['حال'], 'وَهُمْ': ['ليست حالا'] }
    const { rows, correct } = gradeGrid(part, picks)
    expect(rows[0]).toEqual({
      row: 'يَصُدُّونَ',
      options: [
        { option: 'ليست حالا', picked: false, status: '' },
        { option: 'حال', picked: true, status: 'ok' },
      ],
      correct: true,
    })
    expect(rows[1].correct).toBe(false)
    expect(correct).toBe(false)
  })

  it('treats a row with no picks yet as all-missed, not correct', () => {
    expect(gradeGrid(part, {}).correct).toBe(false)
  })
})

describe('isFullyCorrect', () => {
  it('checks a rule entry by its picked set', () => {
    expect(isFullyCorrect({ kind: 'rule', item: rule }, ['a', 'c'])).toBe(true)
    expect(isFullyCorrect({ kind: 'rule', item: rule }, ['a'])).toBe(false)
  })

  it('checks an example entry by its grid picks', () => {
    const picks = { 'يَصُدُّونَ': ['حال'], 'وَهُمْ': ['حال'] }
    expect(isFullyCorrect({ kind: 'example', item: example }, picks)).toBe(true)
    expect(isFullyCorrect({ kind: 'example', item: example }, {})).toBe(false)
  })

  it('needs every ticked part right: a grid and a list, picks kept per letter', () => {
    const two = {
      parts: [
        { letter: 'a', options: ['x', 'y'], rows: ['?'], answer: { '?': ['x'] } },
        { letter: 'b', options: ['A', 'B'], answer: ['B'] },
        { letter: 'd', question: 'Translate', answer: 'text', by: 'claude' },
      ],
    }
    const entry = { kind: 'example', item: two }
    expect(isFullyCorrect(entry, { a: { '?': ['x'] }, b: ['B'] })).toBe(true)
    expect(isFullyCorrect(entry, { a: { '?': ['x'] }, b: ['A', 'B'] })).toBe(false)
    expect(isFullyCorrect(entry, { a: { '?': ['x'] } })).toBe(false)
    expect(gradePart(two.parts[1], { b: ['B'] }).options.map((o) => o.status)).toEqual(['', 'ok'])
  })

  it('reads picks saved before parts were told apart as the grid part\'s', () => {
    const legacy = { 'يَصُدُّونَ': ['حال'], 'وَهُمْ': ['حال'] }
    expect(partPicks(legacy, example.parts[0])).toBe(legacy)
    expect(partPicks(legacy, { letter: 'b', options: ['A'] })).toEqual([])
    // A new save where only another part was ticked is not an old grid save.
    expect(partPicks({ b: ['A'] }, example.parts[0])).toEqual({})
  })

  it('is vacuously true for an example with no grid part', () => {
    expect(isFullyCorrect({ kind: 'example', item: { parts: [] } }, {})).toBe(true)
  })
})

describe('rowName', () => {
  it('shows a label, else the row, else nothing for bare punctuation', () => {
    const part = { rows: ['?1', '?', 'بكر'], labels: { '?1': 'زيد' } }
    expect(part.rows.map((row) => rowName(part, row))).toEqual(['زيد', '', 'بكر'])
    expect(rowName({}, '>')).toBe('')
    expect(rowName({}, '?2')).toBe('?2')
  })
})

describe('narrowQueue, statusOf and scoreOf', () => {
  const other = { ...rule, id: 'r2', tags: ['waw'] }
  const queue = buildQueue([{ key: 'x', rules: [rule, other, { ...rule, id: 'r3' }], examples: [] }])
  const answers = {
    'haal-r01': { picks: ['a', 'c'], checked: true },
    r2: { picks: ['a'], checked: true },
    r3: { picks: ['a'], checked: false },
  }

  it('reads right, wrong and not yet checked', () => {
    expect(queue.map((e) => statusOf(e, answers))).toEqual(['right', 'wrong', ''])
    expect(statusOf(queue[0], {})).toBe('')
  })

  it('narrows by topic and by view', () => {
    const ids = (q) => q.map((e) => e.item.id)
    expect(ids(narrowQueue(queue, answers))).toEqual(['haal-r01', 'r2', 'r3'])
    expect(ids(narrowQueue(queue, answers, { tag: 'haal' }))).toEqual(['haal-r01', 'r3'])
    expect(ids(narrowQueue(queue, answers, { kind: 'rule' }))).toEqual(['haal-r01', 'r2', 'r3'])
    expect(narrowQueue(queue, answers, { kind: 'example' })).toEqual([])
    expect(ids(narrowQueue(queue, answers, { show: 'wrong' }))).toEqual(['r2'])
    expect(ids(narrowQueue(queue, answers, { show: 'todo' }))).toEqual(['r3'])
    expect(narrowQueue(queue, answers, { tag: 'nope' })).toEqual([])
  })

  it('counts a score, and the same question twice counts twice', () => {
    expect(scoreOf(queue, answers)).toEqual({ right: 1, wrong: 1, total: 3 })
    expect(scoreOf([queue[0], queue[0]], answers)).toEqual({ right: 2, wrong: 0, total: 2 })
    expect(scoreOf([], answers)).toEqual({ right: 0, wrong: 0, total: 0 })
  })
})
