// @vitest-environment happy-dom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'

import { renderWithBackend } from '../../test/render'
import { CHOICES, wordsOf } from '../../lib/memorise/memorise'
import { useAnswers, useBookPage, useGaps, useHowYouAnswer, usePageSteps, useArrivedPage, withinPart } from './hooks'

// Two surahs: the first over two printed pages, the second on one.
const WORDS = ['الحمد', 'لله', 'رب', 'العالمين', 'الرحمن', 'الرحيم', 'مالك', 'يوم', 'الدين']
const ayah = (n, page) => ({ ayah: n, arabic: WORDS.slice(n % 3, n % 3 + 6).join(' '), english: '', page })
const surah = (n, pages) => ({ surah: n, name_en: `S${n}`, name_ar: 'س', ayahs: pages.map((page, i) => ayah(i + 1, page)) })
const routes = {
  'GET /quran/surah/1': surah(1, [1, 1, 2, 2]),
  'GET /quran/surah/2': surah(2, [3, 3]),
}

// The panel's own wiring, minus the microphone: answers, how, where, steps and gaps.
const card = { current: null }
function useMemorise() {
  const answers = useAnswers()
  const how = useHowYouAnswer(answers.fresh)
  const where = useBookPage({ fresh: answers.fresh })
  const steps = usePageSteps({ ...where, card })
  const gaps = useGaps({ ...where, ...how, startFrom: 0 })
  return { ...answers, ...how, ...where, ...steps, ...gaps }
}
// Each test opens where the app would on a first visit, not where the last test left the page.
beforeEach(() => { localStorage.clear(); window.history.replaceState(null, '', '/'); card.current = null })

const open = async () => {
  const view = renderWithBackend(useMemorise, { routes })
  await waitFor(() => expect(view.result.current.page).not.toBeNull())
  return view
}

describe('withinPart', () => {
  it('drops the surah a line label repeats, and leaves other labels alone', () => {
    expect(withinPart('3:158')).toBe('158')
    expect(withinPart('12')).toBe('12')
  })
})

describe('useBookPage', () => {
  it('opens on the part a link names, never the first one on the way', async () => {
    const seen = []
    const view = renderWithBackend(() => {
      const where = useBookPage({ fresh: vi.fn(), incoming: '2:1' })
      seen.push(where.part)
      return where
    }, { routes })
    await waitFor(() => expect(view.result.current.page).not.toBeNull())
    expect(view.result.current.part).toBe(2)
    expect(seen).not.toContain(1)
  })
})

describe('useAnswers', () => {
  it('starts an attempt over: answers, marking and shown words all go', () => {
    const { result } = renderHook(useAnswers)
    act(() => {
      result.current.setAnswers({ '0:1': 'x' })
      result.current.setChecked(true)
      result.current.setShown(new Set([2]))
    })
    act(() => result.current.fresh())
    expect(result.current).toMatchObject({ answers: {}, checked: false })
    expect(result.current.shown.size).toBe(0)
  })
})

describe('useHowYouAnswer', () => {
  it('reciting hides words unless nothing is to be missing; every choice starts over', () => {
    const fresh = vi.fn()
    const { result } = renderHook(() => useHowYouAnswer(fresh))
    expect(result.current).toMatchObject({ way: 'type', hidden: false })
    act(() => result.current.chooseWay('recite'))
    expect(result.current.hidden).toBe(true)
    act(() => result.current.chooseDifficulty('none'))
    expect(result.current.hidden).toBe(false)
    const deal = result.current.deal
    act(() => result.current.reDeal())
    expect(result.current.deal).toBe(deal + 1)
    expect(fresh).toHaveBeenCalledTimes(3)
  })
})

describe('useBookPage and usePageSteps', () => {
  it('opens the first surah on its first printed page and fetches the next ahead', async () => {
    const { result, asked } = await open()
    expect(result.current).toMatchObject({ part: 1, pageNumber: 0, atStart: true, atEnd: false })
    expect(result.current.pages).toHaveLength(2)
    expect(result.current.page.map((line) => line.label)).toEqual(['1:1', '1:2'])
    await waitFor(() => expect(asked).toContain('GET /quran/surah/2'))
  })

  it('steps past the last page into the next surah, and back onto the last page', async () => {
    const { result } = await open()
    act(() => result.current.stepPage(1))
    act(() => result.current.stepPage(1))
    await waitFor(() => expect(result.current.page?.[0].label).toBe('2:1'))
    expect(result.current.atStart).toBe(false)
    act(() => result.current.stepPage(-1))
    await waitFor(() => expect(result.current).toMatchObject({ part: 1, pageNumber: 1 }))
  })

  // A page turned from under the page (the buttons there, a swipe) opens at its top.
  it('scrolls a page turned by hand to its top when it began above the screen', async () => {
    const { result } = await open()
    const scrolled = vi.fn()
    card.current = { getBoundingClientRect: () => ({ top: -600 }), scrollIntoView: scrolled }
    act(() => result.current.stepPage(1))
    await waitFor(() => expect(scrolled).toHaveBeenCalledTimes(1))
    expect(scrolled.mock.calls[0][0]).toMatchObject({ block: 'start' })
  })

  it('leaves the scroll alone when the page began on the screen, or turned by itself', async () => {
    const { result } = await open()
    const scrolled = vi.fn()
    card.current = { getBoundingClientRect: () => ({ top: 120 }), scrollIntoView: scrolled }
    act(() => result.current.stepPage(1))
    await waitFor(() => expect(result.current.pageNumber).toBe(1))
    act(() => result.current.openPage(0))
    await waitFor(() => expect(result.current.pageNumber).toBe(0))
    card.current = { getBoundingClientRect: () => ({ top: -600 }), scrollIntoView: scrolled }
    act(() => result.current.openPage(1))
    await waitFor(() => expect(result.current.pageNumber).toBe(1))
    expect(scrolled).not.toHaveBeenCalled()
  })
})

describe('useArrivedPage', () => {
  it('reports another page of the same surah as taking its step\'s place, and a new surah as a step', async () => {
    const onVisit = vi.fn()
    const view = renderWithBackend(() => {
      const where = useBookPage({ fresh: vi.fn() })
      useArrivedPage({ ...where, onVisit, arrival: 0, incoming: null })
      return { ...where, ...usePageSteps({ ...where, card }) }
    }, { routes })
    await waitFor(() => expect(onVisit).toHaveBeenCalledTimes(1))
    expect(onVisit.mock.calls[0][1]).toBe(false)
    act(() => view.result.current.stepPage(1))
    await waitFor(() => expect(onVisit).toHaveBeenCalledTimes(2))
    expect(onVisit.mock.calls[1][1]).toBe(true)
    act(() => view.result.current.stepPage(1))
    await waitFor(() => expect(onVisit).toHaveBeenCalledTimes(3))
    expect(onVisit.mock.calls[2][1]).toBe(false)
  })
})

describe('useGaps', () => {
  it('keeps the gaps still while answering, and moves them on a new deal', async () => {
    const { result } = await open()
    const first = [...result.current.blanks]
    expect(first.length).toBeGreaterThan(0)
    act(() => result.current.setAnswers({ [first[0]]: 'x' }))
    expect([...result.current.blanks]).toEqual(first)
    const dealt = new Set([first.join()])
    for (let i = 0; i < 4; i += 1) {
      act(() => result.current.reDeal())
      dealt.add([...result.current.blanks].join())
    }
    expect(dealt.size).toBeGreaterThan(1)
  })

  it('offers each gap its own word among the choices when picking', async () => {
    const { result } = await open()
    act(() => result.current.chooseWay('pick'))
    const { page, blanks, choices } = result.current
    for (const key of blanks) {
      const [l, w] = key.split(':').map(Number)
      expect(choices.get(key)).toHaveLength(CHOICES)
      expect(choices.get(key)).toContain(wordsOf(page[l].arabic)[w])
    }
  })
})
