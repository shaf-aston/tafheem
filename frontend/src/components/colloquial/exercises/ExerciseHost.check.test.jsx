// @vitest-environment happy-dom
// Answering for real: typing or arranging, then Check (or Enter), marks the answer given.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, describe, expect, it, vi } from 'vitest'

import ExerciseHost from './ExerciseHost'

// No voice on this machine: every word fails to play.
vi.mock('../../../lib/speech/speak', () => ({
  speak: () => Promise.reject(new Error('no voice')), prepare: () => {}, stop: () => {},
}))

afterEach(cleanup)
// An answer is filed with the server; here there is none to reach.
vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response('{}'))))

const typed = { id: 'u.l.reply.01', type: 'reply', prompt: 'Say hello', answer: 'مرحبا', accepted: ['مرحبا', 'marhaba'] }
const arranged = { id: 'u.l.reorder.01', type: 'reorder', prompt: 'Put it in order', answer: 'من أين أنت', accepted: ['من أين أنت'], words: ['أين', 'من', 'أنت'] }
const host = (exercise, onDone) => render(
  <QueryClientProvider client={new QueryClient()}><ExerciseHost exercise={exercise} onDone={onDone} /></QueryClientProvider>,
)

describe('ExerciseHost checking', () => {
  it('marks a typed answer right when Check is pressed', () => {
    const onDone = vi.fn()
    host(typed, onDone)
    fireEvent.change(screen.getByLabelText('Your answer'), { target: { value: 'marhaba' } })
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(onDone).toHaveBeenCalledWith(true, 'marhaba')
  })

  it('gives a typed answer a second go, then marks it wrong; Enter checks it too', () => {
    const onDone = vi.fn()
    host(typed, onDone)
    const box = screen.getByLabelText('Your answer')
    fireEvent.change(box, { target: { value: 'xyz' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    // The first miss is a second go, not a mark: nothing filed, the answer not yet shown.
    expect(onDone).not.toHaveBeenCalled()
    expect(screen.getByText(/have one more go/)).toBeTruthy()
    expect(screen.queryByText(/The natural answer is/)).toBeNull()
    fireEvent.change(box, { target: { value: 'xyzz' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(onDone).toHaveBeenCalledWith(false, 'xyzz')
    expect(screen.getByText(/The natural answer is/)).toBeTruthy()
  })

  it('checks an arranged answer', () => {
    const onDone = vi.fn()
    host(arranged, onDone)
    for (const word of ['من', 'أين', 'أنت']) fireEvent.click(screen.getAllByRole('button', { name: word })[0])
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(onDone).toHaveBeenCalledWith(true, ['من', 'أين', 'أنت'])
  })

  it('shows a heard question\'s spelling when no voice can say it', async () => {
    host({ id: 'u.l.word.2.listen', type: 'choose', prompt: 'Which word did you hear?', answer: 'شكرا', options: ['شكرا', 'مرحبا'], say: 'شكرا', spelling: 'shukran' })
    expect(screen.queryByText('shukran')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Say it aloud' }))
    expect(await screen.findByText('shukran')).toBeTruthy()
    expect(screen.getByText(/No sound here/)).toBeTruthy()
  })

  it('asks for Arabic letters, without marking, when the answer has no Latin spelling', () => {
    const onDone = vi.fn()
    host({ id: 'u.l.reply.02', type: 'reply', prompt: 'How are you? (to a woman)', answer: 'كويسة', accepted: ['كويسة'] }, onDone)
    const box = screen.getByLabelText('Your answer')
    expect(box.getAttribute('placeholder')).toBe('Type it in Arabic letters')
    fireEvent.change(box, { target: { value: 'kwayyisa' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(screen.getByText(/in Arabic letters/, { selector: '[role=status]' })).toBeTruthy()
    expect(onDone).not.toHaveBeenCalled()
    fireEvent.change(box, { target: { value: 'كويسه' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(onDone).toHaveBeenCalledWith(true, 'كويسه')
  })
})
