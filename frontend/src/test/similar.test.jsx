// @vitest-environment happy-dom
// Similar verses on a fake backend: Start opens what is due, a twin that reads
// the same is told apart by what follows, a link with a verse opens that verse,
// and the reader's study shows the way in.
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import SimilarPanel from '../components/SimilarPanel'
import AyahStudy from '../components/quran/AyahStudy'

const SURAH = {
  surah: 27,
  ayahs: [3, 4],
  groups: [
    { id: 1, keys: ['27:3', '31:4'], pairs: [['27:3', '31:4']], change_type: '', sources: [] },
    { id: 2, keys: ['27:4', '16:22'], pairs: [['27:4', '16:22']], change_type: 'replacement', sources: [] },
  ],
}
const SAME = {
  surah: 27, ayah: 3, text: 'ا ب ج', after: 'د ه و ز',
  partners: [{ key: '31:4', surah: 31, ayah: 4, text: 'ا ب ج', after: 'ط ي ك ل', diff_self: [], diff_other: [], changes: [], change_type: '', sources: [] }],
}
const WORDED = {
  surah: 27, ayah: 4, text: 'ا ب ج', after: 'م',
  partners: [{ key: '16:22', surah: 16, ayah: 22, text: 'ا ق ج', after: 'ن', diff_self: [[1, 2]], diff_other: [[1, 2]], changes: [{ self: [1, 2], other: [1, 2] }], change_type: 'replacement', sources: [] }],
}
const ROUTES = {
  'GET /quran/similar/surah/27': SURAH,
  'GET /quran/similar/27/3': SAME,
  'GET /quran/similar/27/4': WORDED,
  'GET /progress/summary': { items: [{ item: '27:3~31:4', known: true, due: false }, { item: '16:22~27:4', known: true, due: true }] },
  'POST /progress/attempts': { earned: 1 },
}

describe('similar verses', () => {
  it('starts with what is due, and a passed drill files the pair', async () => {
    localStorage.setItem('similar-surah', '27')
    const { asked } = renderScreen(<SimilarPanel accent="#0a7" incoming={null} arrival={null} onVisit={() => {}} />, { routes: ROUTES })
    const start = await screen.findByRole('button', { name: 'Review what is due' })
    fireEvent.click(start)
    expect(await screen.findByText('Question 1 of 2')).toBeTruthy()
    // the gap is the second word; its own wording is right
    fireEvent.click(screen.getByRole('button', { name: 'ب' }))
    expect(await screen.findByText('Right.')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    fireEvent.click(screen.getByRole('button', { name: 'ق' }))
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(await screen.findByText('All correct: this pair is mastered.')).toBeTruthy()
    expect(asked).toContain('POST /progress/attempts')
  })

  it('tells twins that read the same apart by what follows, in Compare and in Drill', async () => {
    localStorage.setItem('similar-surah', '27')
    renderScreen(<SimilarPanel accent="#0a7" incoming="27:3" arrival={1} onVisit={() => {}} />, { routes: ROUTES })
    expect(await screen.findByText(/read word for word the same/)).toBeTruthy()
    expect(screen.getByText('د ه و ز')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Drill this pair' }))
    expect(await screen.findByText(/What comes after this in/)).toBeTruthy()
    expect(screen.getByRole('button', { name: 'ط ي ك ل' })).toBeTruthy()
  })

  it('names the change type on a worded pair and the Browse sheet on a phone', async () => {
    localStorage.setItem('similar-surah', '27')
    window.matchMedia = (q) => ({ matches: q.includes('max-width'), addEventListener() {}, removeEventListener() {} })
    renderScreen(<SimilarPanel accent="#0a7" incoming="27:4" arrival={2} onVisit={() => {}} />, { routes: ROUTES })
    expect(await screen.findByText(/a different word/)).toBeTruthy()
    expect(screen.getByText('Pair 2 of 2')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Browse' }))
    expect(await screen.findByRole('dialog')).toBeTruthy()
    delete window.matchMedia
  })

  it('shows the way in from the ayah study', async () => {
    const onGo = vi.fn()
    renderScreen(<AyahStudy surah={27} ayah={3} onGo={onGo} onClose={() => {}} accent="#0a7" />, {
      routes: { ...ROUTES, 'GET /quran/27/3': { words: [{ arabic: 'ا', position: 1 }] } },
    })
    fireEvent.click(await screen.findByRole('button', { name: '1 look-alike' }))
    expect(onGo).toHaveBeenCalledWith('similar', '27:3')
  })
})
