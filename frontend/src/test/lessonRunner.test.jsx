// @vitest-environment happy-dom
// The lesson runner's feel: three right in a row shows a run, a wrong answer ends it, and the end screen says how many
// were right first time, how long it took and what was missed, and offers the next lesson. Enter checks and goes on,
// also from an option; leaving mid-lesson asks first, and Escape stays. While it runs the lesson holds focus mode, and
// Check gives a verdict panel ("Correct" / "Not quite" and one line); a Qur'anic word shows its ayah.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import LessonRunner from '../components/practice/LessonRunner'

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

  it("says what the picked wrong option got wrong, and that it comes back only the first time", () => {
    const card = { ...choose('w'), wrong: { 1: 'Wrong one: no ال.' } }
    renderScreen(<LessonRunner cards={[card]} accent="#26c" onLeave={() => {}} />, { routes: { 'POST /progress/attempts': { earned: 0 } } })
    fireEvent.click(screen.getByRole('radio', { name: 'wrong w' }))
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(screen.getByRole('status').textContent).toBe('Not quite Wrong one: no ال. It comes back at the end.')
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(screen.getByText('Again')).toBeTruthy()
    fireEvent.click(screen.getByRole('radio', { name: 'wrong w' }))
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(screen.getByRole('status').textContent).toBe('Not quite Wrong one: no ال.')
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    // The recap says what this reader got wrong, not the general rule.
    expect(screen.getByText('Wrong one: no ال.')).toBeTruthy()
  })

  it('shows XP when there is a reading of it, and tells a guest it is this device\'s until they log in', () => {
    const { unmount } = renderScreen(<LessonRunner cards={[choose('a')]} accent="#26c" onLeave={() => {}} />, { routes: { 'POST /progress/attempts': { earned: 0 } } })
    answer('a', 'right')
    expect(screen.queryByText('XP')).toBe(null)
    expect(screen.queryByText(/Log in/)).toBe(null)
    unmount()
    renderScreen(<LessonRunner cards={[choose('a')]} accent="#26c" rewards={{ level: 2, into: 5, need: 20 }} guest onLeave={() => {}} />,
      { routes: { 'POST /progress/attempts': { earned: 2 } } })
    answer('a', 'right')
    expect(screen.getByText('XP')).toBeTruthy()
    expect(screen.getByText('Log in to keep your XP and streak on any device.')).toBeTruthy()
  })

  it('recaps a missed gap card with its line, the gap filled with the right word', () => {
    const gap = { ...choose('g'), ask: 'Which word completes the line?', ar: 'الحمد ____ رب العالمين',
      options: [{ id: '0', text: 'لله' }, { id: '1', text: 'wrong g' }] }
    renderScreen(<LessonRunner cards={[gap]} accent="#26c" onLeave={() => {}} />, { routes: { 'POST /progress/attempts': { earned: 0 } } })
    answer('g', 'wrong')
    fireEvent.click(screen.getByRole('radio', { name: 'لله' }))
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(screen.getByText('الحمد لله رب العالمين')).toBeTruthy()
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
    expect(screen.getByRole('status').textContent).toMatch(/^Correct/)
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
    expect(screen.getByRole('status').textContent).toMatch(/^Correct/)
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

  it('holds focus mode while the lesson runs, and gives it back on the end screen and on leaving', () => {
    const focus = () => document.documentElement.dataset.focus
    const { unmount } = renderScreen(<LessonRunner cards={[choose('a')]} accent="#26c" onLeave={() => {}} />,
      { routes: { 'POST /progress/attempts': { earned: 0 } } })
    expect(focus()).toBe('lesson')
    answer('a', 'right')
    expect(screen.getByText('Lesson done')).toBeTruthy()
    expect(focus()).toBe(undefined)
    unmount()
    const again = renderScreen(<LessonRunner cards={[choose('a')]} accent="#26c" onLeave={() => {}} />)
    expect(focus()).toBe('lesson')
    again.unmount()
    expect(focus()).toBe(undefined)
  })

  it('says the verdict and the meaning, right or wrong, and marks the pick', () => {
    const meaning = {
      id: 'm', kind: 'meaning', tag: 'New word', answerText: 'the book',
      question: { prompt: 'الكتاب', answerId: 'k', options: [{ id: 'k', text: 'the book' }, { id: 'p', text: 'the pen' }] },
      record: { module: 'test', item: 'm' },
    }
    renderScreen(<LessonRunner cards={[meaning]} accent="#26c" onLeave={() => {}} />, { routes: { 'POST /progress/attempts': { earned: 0 } } })
    expect(screen.getByRole('button', { name: 'Check' }).disabled).toBe(true)
    fireEvent.click(screen.getByRole('radio', { name: 'the pen' }))
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(screen.getByRole('status').textContent).toBe('Not quite It means: the book. It comes back at the end.')
    expect(screen.getByRole('radio', { name: 'the pen' }).dataset.mark).toBe('wrong')
    expect(screen.getByRole('radio', { name: 'the book' }).dataset.mark).toBe('right')
    expect(document.querySelector('.grow-lesson-foot').dataset.result).toBe('wrong')
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    fireEvent.click(screen.getByRole('radio', { name: 'the book' }))
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(screen.getByRole('status').textContent).toBe('Correct It means: the book.')
    expect(document.querySelector('.grow-lesson-foot').dataset.result).toBe('right')
  })

  it("shows a Qur'anic word in its ayah, marked, with a way to hear it", async () => {
    const meaning = {
      id: 'q', kind: 'meaning', tag: 'New word', answerText: 'Lord',
      question: { prompt: 'رَبِّ', answerId: 'r', ayah: [1, 2, 3], options: [{ id: 'r', text: 'Lord' }, { id: 'p', text: 'praise' }] },
      record: { module: 'test', item: 'q' },
    }
    const words = ['ٱلْحَمْدُ', 'لِلَّهِ', 'رَبِّ', 'ٱلْعَـٰلَمِينَ'].map((uthmani, i) => ({ position: `1:2:${i + 1}`, uthmani }))
    renderScreen(<LessonRunner cards={[meaning]} accent="#26c" onLeave={() => {}} />, { routes: { 'GET /quran/1/2': { words } } })
    expect((await screen.findByRole('button', { name: /Listen/ })).textContent).toMatch(/1:2/)
    expect(document.querySelector('.grow-ayah-line mark').textContent).toBe('رَبِّ')
  })
})
