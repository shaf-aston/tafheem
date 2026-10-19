// @vitest-environment happy-dom
// Practising Tamreen: tick what is true and check, and the verdict comes up in
// words, every option is marked and locked, and the score line counts it.
import { beforeEach, describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import TamreenPractise from '../components/nahw/TamreenPractise'

const RULE = (id, answer) => ({ id, question: `Question ${id}`, options: ['A', 'B', 'C'], answer, tags: ['hal'] })
const exercises = [{ key: 'one', rules: [RULE('r1', ['A']), RULE('r2', ['C'])] }]
const tags = [{ key: 'hal', en: 'Hal', ar: 'الحال' }]

// Answers are saved in the browser; each test starts with none.
beforeEach(() => localStorage.clear())

describe('Tamreen practise', () => {
  it('checks a wrong answer, then a right one', async () => {
    renderScreen(<TamreenPractise exercises={exercises} tags={tags} accent="#0a7" onProgress={() => {}} onNotes={() => {}} />)
    expect(await screen.findByText('Question r1')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'B' }))
    expect(screen.getByRole('button', { name: 'B' }).getAttribute('aria-pressed')).toBe('true')
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))

    expect(await screen.findByText('Not quite')).toBeTruthy()
    // Each option says how it went, and none can be changed any more.
    const marked = ['B Not true', 'A You missed this', 'C'].map((name) => screen.getByRole('button', { name }))
    expect(marked.every((option) => option.disabled)).toBe(true)
    expect(screen.getByText('answered', { exact: false }).textContent).toContain('0/1')

    fireEvent.click(screen.getByRole('button', { name: 'Next question' }))
    expect(await screen.findByText('Question r2')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'C' }))
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(await screen.findByRole('button', { name: 'C Right' })).toBeTruthy()
    // Said twice: beside the option, and as the verdict.
    expect(screen.getAllByText('Right')).toHaveLength(2)
    expect(screen.queryByText('Not quite')).toBeNull()
    expect(screen.getByText('answered', { exact: false }).textContent).toContain('1/2')
  })
})
