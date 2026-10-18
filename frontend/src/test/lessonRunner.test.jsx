// @vitest-environment happy-dom
// The lesson runner's feel: three right in a row shows a run, a wrong answer ends it, and the end screen says how many
// were right first time, how long it took and what was missed, and offers the next lesson. Enter checks and goes on,
// also from an option; leaving mid-lesson asks first, and Escape stays.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import LessonRunner from '../components/grow/LessonRunner'

const choose = (id) => ({
  id, kind: 'choose', tag: 'Test', ask: `Question ${id}?`, why: 'Because.', answer: '0',
  options: [{ id: '0', text: `right ${id}` }, { id: '1', text: `wrong ${id}` }],
  record: { module: 'test', item: id },
})

const answer = (id, pick) => {
  fireEvent.click(screen.getByRole('radio', { name: `${pick} ${id}` }))
  fireEvent.click(screen.getByRole('button', { name: 'Check' }))
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
}

describe('lesson runner', () => {
  it('shows a run from three right, ends it on a wrong one, and sums the lesson at the end', () => {
    renderScreen(<LessonRunner cards={['a', 'b', 'c', 'd'].map(choose)} accent="#26c" onLeave={() => {}} />, {
      routes: { 'POST /progress/attempts': { earned: 0 } },
    })
    answer('a', 'right')
    answer('b', 'right')
    expect(screen.queryByText(/in a row/)).toBe(null)
    answer('c', 'right')
    expect(screen.getByText('3 in a row')).toBeTruthy()
    answer('d', 'wrong')
    expect(screen.queryByText(/in a row/)).toBe(null)
    // The wrong one comes back once at the end; right this time, it does not change the first-time score.
    answer('d', 'right')
    expect(screen.getByText('Lesson done')).toBeTruthy()
    expect(screen.getByText('3/4')).toBeTruthy()
    expect(screen.getByText(/^\d+:\d\d$/)).toBeTruthy()
    // The one missed first time is recapped with its reason.
    expect(screen.getByRole('heading', { name: 'What you missed' })).toBeTruthy()
    expect(screen.getByText('Question d?')).toBeTruthy()
  })

  it('offers the next lesson at the end, and the way back to the path', () => {
    const went = []
    renderScreen(<LessonRunner cards={[choose('a')]} accent="#26c" next={{ title: 'Ghusl', go: () => went.push('next') }}
      onLeave={() => went.push('back')} />, { routes: { 'POST /progress/attempts': { earned: 0 } } })
    answer('a', 'right')
    expect(screen.queryByRole('heading', { name: 'What you missed' })).toBe(null)
    fireEvent.click(screen.getByRole('button', { name: 'Next: Ghusl' }))
    fireEvent.click(screen.getByRole('button', { name: 'Back to the path' }))
    expect(went).toEqual(['next', 'back'])
  })

  it('checks and goes on with Enter, focusing Continue after Check', () => {
    renderScreen(<LessonRunner cards={['a', 'b'].map(choose)} accent="#26c" onLeave={() => {}} />, {
      routes: { 'POST /progress/attempts': { earned: 0 } },
    })
    fireEvent.click(screen.getByRole('radio', { name: 'right a' }))
    fireEvent.keyDown(document.body, { key: 'Enter' })
    expect(screen.getByRole('status').textContent).toMatch(/^Right!/)
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Continue' }))
    fireEvent.keyDown(document.body, { key: 'Enter' })
    expect(screen.getByText('Question b?')).toBeTruthy()
  })

  it('checks with Enter from the option just clicked, once an answer is ready', () => {
    renderScreen(<LessonRunner cards={['a'].map(choose)} accent="#26c" onLeave={() => {}} />, {
      routes: { 'POST /progress/attempts': { earned: 0 } },
    })
    const right = screen.getByRole('radio', { name: 'right a' })
    fireEvent.keyDown(right, { key: 'Enter' })
    expect(screen.queryByRole('status')).toBe(null)
    fireEvent.click(right)
    fireEvent.keyDown(right, { key: 'Enter' })
    expect(screen.getByRole('status').textContent).toMatch(/^Right!/)
  })

  it('asks before leaving once a question is answered, and leaves at once before', () => {
    const went = []
    renderScreen(<LessonRunner cards={['a', 'b'].map(choose)} accent="#26c" onLeave={() => went.push('left')} />, {
      routes: { 'POST /progress/attempts': { earned: 0 } },
    })
    answer('a', 'right')
    fireEvent.click(screen.getByRole('button', { name: 'Leave the lesson' }))
    expect(screen.getByRole('alertdialog')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Keep going' }))
    expect(screen.queryByRole('alertdialog')).toBe(null)
    fireEvent.click(screen.getByRole('button', { name: 'Leave the lesson' }))
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Keep going' }))
    fireEvent.keyDown(document.body, { key: 'Escape' })
    expect(screen.queryByRole('alertdialog')).toBe(null)
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Leave the lesson' }))
    fireEvent.click(screen.getByRole('button', { name: 'Leave the lesson' }))
    fireEvent.click(screen.getByRole('button', { name: 'Leave' }))
    expect(went).toEqual(['left'])
  })
})
