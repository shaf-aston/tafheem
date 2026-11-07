// @vitest-environment happy-dom
// Saving a Qur'an word from its card: the toggle says where it goes, the word
// comes back in the quiz's Review pile, and unsaving takes it out again.
import { beforeEach, describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import { wordsFor } from '../../lib/quiz/quizBanks'
import { readSavedWords } from '../../lib/quiz/savedWords'
import WordCard from './WordCard'

// A real word of the shipped table (public/words): أَوَّل is "first".
const WORD = { position: '57:3:1', arabic: 'هُوَ ٱلْأَوَّلُ', lemma: 'أَوَّل', root: 'أول', type: 'ism', grammar: ['noun'] }
const ROUTES = { 'GET /progress/review': { items: [] }, 'GET /progress/summary': { items: [] } }
const reviewKeys = async () => (await wordsFor('review', '', 'en')).map((w) => w.meaningKey)

describe('Save word for review', () => {
  beforeEach(() => localStorage.clear())

  it('saves, says so, brings the word back in Review, and unsaves', async () => {
    renderScreen(<WordCard word={WORD} onClose={() => {}} onGo={() => {}} exclude="quran" />, { routes: ROUTES })
    const save = await screen.findByRole('button', { name: 'Save' })
    expect(save.getAttribute('aria-pressed')).toBe('false')
    fireEvent.click(save)

    expect(screen.getByRole('status').textContent).toBe('Saved → comes back in Review')
    expect(screen.getByRole('button', { name: 'Saved' }).getAttribute('aria-pressed')).toBe('true')
    expect(readSavedWords()).toEqual([{ key: 'first', lemma: 'أَوَّل' }])
    expect(await reviewKeys()).toEqual(['first'])

    fireEvent.click(screen.getByRole('button', { name: 'Saved' }))
    expect(screen.getByRole('button', { name: 'Save' })).toBeTruthy()
    expect(readSavedWords()).toEqual([])
    expect(await reviewKeys()).toEqual([])
  })

  it('offers nothing for a word that is not from the Qur\'an', async () => {
    renderScreen(<WordCard word={{ ...WORD, position: '1' }} onClose={() => {}} onGo={() => {}} />, { routes: ROUTES })
    await screen.findByRole('button', { name: 'Conjugate' })
    expect(screen.queryByRole('button', { name: 'Save' })).toBeNull()
  })
})
