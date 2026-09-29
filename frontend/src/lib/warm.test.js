import { QueryClient } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

import { onHover, warm } from './warm'

const query = (fn) => ({ queryKey: ['k'], queryFn: fn })

describe('warm', () => {
  it('prefetches once the page is idle', async () => {
    const fn = vi.fn().mockResolvedValue(1)
    const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
    warm(client, query(fn))
    expect(fn).not.toHaveBeenCalled()
    await vi.waitFor(() => expect(fn).toHaveBeenCalledTimes(1))
  })

  it('does not fetch what is already cached', async () => {
    const fn = vi.fn().mockResolvedValue(1)
    const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
    await client.prefetchQuery(query(fn))
    onHover(client, query(fn)).onPointerEnter()
    warm(client, query(fn))
    await new Promise((r) => setTimeout(r, 300))
    expect(fn).toHaveBeenCalledTimes(1)
  })
})
