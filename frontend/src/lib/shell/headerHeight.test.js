// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest'
import { act, renderHook } from '@testing-library/react'

import { setHeaderHeight, useHeaderHeight } from './headerHeight'

describe('headerHeight', () => {
  it('publishes the height to CSS and to readers, and tells them when it changes', () => {
    const { result } = renderHook(() => useHeaderHeight())
    act(() => setHeaderHeight(64))
    expect(result.current).toBe(64)
    expect(document.documentElement.style.getPropertyValue('--app-header-h')).toBe('64px')
    act(() => setHeaderHeight(96))
    expect(result.current).toBe(96)
  })
})
