// @vitest-environment happy-dom
import { describe, expect, it, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { useLineTranslations } from './useLineTranslations'

const wrapper = ({ children }) => (
  <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
)
const busy = () => Object.assign(new Error('busy'), { response: { status: 429 } })

describe('useLineTranslations', () => {
  it('translates each Arabic line once and skips the rest', async () => {
    const ask = vi.fn(async (text) => ({ meaning: `m:${text}` }))
    const lines = [{ text: 'ذهب الولد' }, { text: 'ذهب الولد' }, { text: '123' }]
    const { result } = renderHook(() => useLineTranslations(lines, { ask }), { wrapper })
    await waitFor(() => expect(result.current['ذهب الولد']?.state).toBe('done'))
    expect(result.current['ذهب الولد'].data.meaning).toBe('m:ذهب الولد')
    expect(result.current['123']).toBeUndefined()
    expect(ask).toHaveBeenCalledTimes(1)
  })

  it('waits on a 429 and asks again', async () => {
    let calls = 0
    const ask = vi.fn(async () => { if (++calls === 1) throw busy(); return { meaning: 'ok' } })
    const lines = [{ text: 'قال' }]
    const { result } = renderHook(() => useLineTranslations(lines, { ask, pausedMs: 5 }), { wrapper })
    await waitFor(() => expect(result.current['قال']?.state).toBe('done'))
    expect(ask).toHaveBeenCalledTimes(2)
  })

  it('gives up after three busy answers, and at once on any other error', async () => {
    const ask = vi.fn(async (text) => { throw text === 'قال' ? busy() : new Error('down') })
    const lines = [{ text: 'قال' }, { text: 'كتب' }]
    const { result } = renderHook(() => useLineTranslations(lines, { ask, pausedMs: 1 }), { wrapper })
    await waitFor(() => expect(result.current['قال']?.state).toBe('failed'))
    await waitFor(() => expect(result.current['كتب']?.state).toBe('failed'))
    expect(ask.mock.calls.filter(([text]) => text === 'قال')).toHaveLength(3)
    expect(ask.mock.calls.filter(([text]) => text === 'كتب')).toHaveLength(1)
  })
})
