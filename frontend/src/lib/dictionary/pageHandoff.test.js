import { describe, expect, it, vi } from 'vitest'

import { handPage, onPageHanded, takePage } from './pageHandoff'

describe('pageHandoff', () => {
  it('keeps a handed picture until it is taken, once', () => {
    const picture = new File(['x'], 'page.png', { type: 'image/png' })
    handPage(picture)
    expect(takePage()).toBe(picture)
    expect(takePage()).toBeNull()
  })

  it('tells a listener when a picture is handed, until it stops listening', () => {
    const heard = vi.fn()
    const stop = onPageHanded(heard)
    handPage(new File(['x'], 'a.png', { type: 'image/png' }))
    stop()
    handPage(new File(['x'], 'b.png', { type: 'image/png' }))
    expect(heard).toHaveBeenCalledTimes(1)
    expect(takePage().name).toBe('b.png')
  })
})
