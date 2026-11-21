// @vitest-environment happy-dom
import { describe, expect, it, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { useLineTranslations } from './useLineTranslations'

const wrapped = (client = new QueryClient()) => ({ children }) => (
  <QueryClientProvider client={client}>{children}</QueryClientProvider>
)
const busy = () => Object.assign(new Error('busy'), { response: { status: 429 } })
const answer = vi.fn(async (texts) => texts.map((text) => ({ meaning: `m:${text}` })))
const allDone = (found) => Object.values(found).length > 0 && Object.values(found).every((one) => one.state === 'done')

describe('useLineTranslations', () => {
  it('translates each Arabic line once and skips the rest', async () => {
    const ask = vi.fn(answer)
    const lines = [{ text: 'ذهب الولد' }, { text: 'ذهب الولد' }, { text: '123' }, { text: 'ص. ٣' }]
    const { result } = renderHook(() => useLineTranslations(lines, { ask }), { wrapper: wrapped() })
    await waitFor(() => expect(result.current['ذهب الولد']?.state).toBe('done'))
    expect(result.current['ذهب الولد'].data.meaning).toBe('m:ذهب الولد')
    expect(result.current['123']).toBeUndefined()
    expect(result.current['ص. ٣']).toBeUndefined()
    expect(ask).toHaveBeenCalledTimes(1)
  })

  it('sends the lines in batches, in page order', async () => {
    const ask = vi.fn(answer)
    const lines = ['قال', 'كتب', 'ذهب', 'رجع', 'جلس'].map((text) => ({ text }))
    const { result } = renderHook(() => useLineTranslations(lines, { ask, batch: 2, together: 1 }), { wrapper: wrapped() })
    await waitFor(() => expect(allDone(result.current)).toBe(true))
    expect(ask.mock.calls.map(([texts]) => texts)).toEqual([['قال', 'كتب'], ['ذهب', 'رجع'], ['جلس']])
    expect(result.current['رجع'].data.meaning).toBe('m:رجع')
  })

  it('asks only for lines not already answered', async () => {
    const client = new QueryClient()
    client.setQueryData(['sentence', 'قال'], { meaning: 'kept' })
    const ask = vi.fn(answer)
    const lines = [{ text: 'قال' }, { text: 'كتب' }]
    const { result } = renderHook(() => useLineTranslations(lines, { ask }), { wrapper: wrapped(client) })
    await waitFor(() => expect(allDone(result.current)).toBe(true))
    expect(ask.mock.calls).toEqual([[['كتب']]])
    expect(result.current['قال'].data.meaning).toBe('kept')
    expect(client.getQueryData(['sentence', 'كتب']).meaning).toBe('m:كتب')
  })

  it('waits on a 429 and asks again', async () => {
    let calls = 0
    const ask = vi.fn(async (texts) => { if (++calls === 1) throw busy(); return answer(texts) })
    const { result } = renderHook(() => useLineTranslations([{ text: 'قال' }], { ask, pausedMs: 5 }), { wrapper: wrapped() })
    await waitFor(() => expect(result.current['قال']?.state).toBe('done'))
    expect(ask).toHaveBeenCalledTimes(2)
  })

  it('gives up after its busy tries, and at once on any other error', async () => {
    const ask = vi.fn(async ([text]) => { throw text === 'قال' ? busy() : new Error('down') })
    const lines = [{ text: 'قال' }, { text: 'كتب' }]
    const { result } = renderHook(() => useLineTranslations(lines, { ask, batch: 1, pausedMs: 1, tries: 3 }), { wrapper: wrapped() })
    await waitFor(() => expect(result.current['قال']?.state).toBe('failed'))
    await waitFor(() => expect(result.current['كتب']?.state).toBe('failed'))
    expect(ask.mock.calls.filter(([[text]]) => text === 'قال')).toHaveLength(3)
    expect(ask.mock.calls.filter(([[text]]) => text === 'كتب')).toHaveLength(1)
  })

  it('pauses every batch together on a 429, not each on its own', async () => {
    let first = true
    const asked = []
    const ask = vi.fn(async (texts) => {
      asked.push(Date.now())
      if (first) { first = false; throw busy() }
      return answer(texts)
    })
    const lines = ['قال', 'كتب', 'ذهب', 'رجع'].map((text) => ({ text }))
    const { result } = renderHook(() => useLineTranslations(lines, { ask, batch: 1, pausedMs: 60, together: 1 }), { wrapper: wrapped() })
    await waitFor(() => expect(allDone(result.current)).toBe(true))
    expect(asked[1] - asked[0]).toBeGreaterThanOrEqual(50)
    expect(ask).toHaveBeenCalledTimes(5)
  })
})
