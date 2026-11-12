import { describe, expect, it } from 'vitest'

import { ENGLISH, englishQuery, shownView } from './entryEnglish'

const failure = (status) => ({ response: { status, data: {} } })

describe('shownView', () => {
  it('shows the chosen view once the reader has pressed', () => {
    for (const view of ['words', 'together', 'one']) expect(shownView(view, true, {})).toBe(view)
  })

  // Opened on its own (a wide screen): only English already kept, never a model call nobody pressed for.
  it('opened on its own, shows only English already kept', () => {
    expect(shownView('together', false, {})).toBe('together')
    expect(shownView('words', false, { senses_kept: true })).toBe('words')
    expect(shownView('words', false, { senses_kept: false })).toBe('together')
    expect(shownView('one', false, { english_kept: true })).toBe('together')
  })
})

describe('englishQuery', () => {
  it('asks once more for lines after a failure, never after a refusal', () => {
    const { retry } = englishQuery(ENGLISH.lines, 'كتب')
    expect(retry(0, failure(502))).toBe(true)
    expect(retry(0, failure(429))).toBe(false)
  })

  it('never asks again for the shapes with no retry', () => {
    expect(englishQuery(ENGLISH.together, 'كتب').retry).toBe(false)
    expect(englishQuery(ENGLISH.words, 'كتب').retry).toBe(false)
  })
})
