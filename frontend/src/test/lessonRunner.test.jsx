// @vitest-environment happy-dom
// The lesson runner's feel: three right in a row shows a run, a wrong answer ends it, and the end screen says how many
// were right first time, how long it took and what was missed, and offers the next lesson.
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
})
