// @vitest-environment happy-dom
// An analysed sentence is written out once, in the tree; its English and the
// tools close the tree's card instead of a second card and a row of their own.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen, within } from '@testing-library/react'

import { renderScreen } from './render'
import IraabAnalyzer from '../components/nahw/IraabAnalyzer'

const SENTENCE = 'الكِتَابُ مُفِيدٌ'
const source = { key: 'nahw', label: 'Nahw rule engine', confidence: 'derived', detail: '' }
const word = (w, role, role_key) => ({ word: w, role, role_key, name: null, case: "raf'", sign: 'ضمة', reason: '', governor: null, follows: null })
const leaf = (role, i) => ({ role, word: i, children: [], parts: [] })
const ANALYSIS = {
  sentence: SENTENCE,
  words: [word('الكِتَابُ', 'مبتدأ', 'mubtada'), word('مُفِيدٌ', 'خبر', 'khabar')],
  summary: 'جُمْلَةٌ اِسْمِيَّةٌ',
  source,
  tree: { words: ['الكِتَابُ', 'مُفِيدٌ'], coverage: 1, tree: { label: 'جُمْلَةٌ اِسْمِيَّةٌ', children: [leaf('مبتدأ', 0), leaf('خبر', 1)], parts: [] } },
}
const MEANING = { query: SENTENCE, kind: 'sentence', direction: 'ar', meaning: 'A useful book, this', source, ref: null, words: [], left_out: [] }

const PRACTICE = { questions: [{ question: 'What is the khabar?', answer: 'مُفِيدٌ', hint: '' }], source }
const routes = { 'POST /analyze': ANALYSIS, 'GET /dictionary/sentence': MEANING, 'POST /practice': PRACTICE }

describe('Nahw answer', () => {
  it('puts the English and the tools in the foot of the tree card', async () => {
    renderScreen(<IraabAnalyzer analyse={SENTENCE} />, { routes })
    const english = await screen.findByText('A useful book, this')
    // The nearest box holding both the English and the tree: the tree's card, not the page.
    let card = english
    while (!card.querySelector('.tk-frame')) card = card.parentElement
    expect(card.querySelector('.word')).toBeNull()
    expect(card.contains(screen.getByRole('button', { name: 'Copy' }))).toBe(true)
    expect(card.contains(screen.getByRole('button', { name: 'Show larger' }))).toBe(true)
  })

  it('does not write the whole sentence out again under the tree', async () => {
    const { container } = renderScreen(<IraabAnalyzer analyse={SENTENCE} />, { routes })
    await screen.findByText('A useful book, this')
    // The answer holds the sentence's words, in the tree and the cards, never the sentence whole.
    expect(within(container.querySelector('[aria-live]')).queryByText(SENTENCE)).toBeNull()
  })

  it('draws the extras as one list of rows, the page\'s own after the sentence\'s', async () => {
    renderScreen(<IraabAnalyzer analyse={SENTENCE} more={<details><summary>Page extra</summary></details>} />, { routes })
    await screen.findByText('A useful book, this')
    const rows = [...screen.getByText('Page extra').closest('div').children].map((d) => d.querySelector('summary').textContent)
    expect(rows).toEqual(['Full tableEvery word, side by side', 'Practice questionsCheck you followed this sentence', 'Page extra'])
  })

  it('makes practice questions the first time the row opens', async () => {
    renderScreen(<IraabAnalyzer analyse={SENTENCE} />, { routes })
    await screen.findByText('A useful book, this')
    const row = screen.getByText('Practice questions').closest('details')
    row.open = true
    fireEvent(row, new Event('toggle'))
    expect(await screen.findByText('1. What is the khabar?')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'New questions' })).toBeTruthy()
  })
})
