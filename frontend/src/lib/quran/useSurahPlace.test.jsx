// @vitest-environment happy-dom
import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import QURAN from '../../config/quran.json'
import { useSurahPlace } from './useSurahPlace'

const { split: SPLIT } = QURAN

// A list as the browser would lay it out: rows 100px tall, its scroll position settable, no layout needed.
function fakeList(rows = 50, scrollTop = 0) {
  const children = Array.from({ length: rows }, (_, i) => ({ offsetTop: i * 100, querySelector: () => ({ focus: vi.fn() }) }))
  return { children, scrollTop }
}

const data = { ayah_count: 50 }
// Phone width: the study stacks under the surah.
const phone = () => { globalThis.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} }) }

function mount(place, onPlace = vi.fn()) {
  const view = renderHook((props) => useSurahPlace(props.place, data, props.onPlace, vi.fn()), { initialProps: { place, onPlace } })
  view.result.current.list.current = fakeList(50, 3000)
  return view
}

describe('useSurahPlace: the study sheet', () => {
  beforeEach(phone)

  it('a study taken full screen is given its usual size back, a size the reader dragged to is kept', () => {
    const onPlace = vi.fn()
    const { result } = mount({ surah: 2, ayah: 5 }, onPlace)
    act(() => result.current.sheet.onFull())
    expect(result.current.share).toBe(QURAN.split.full)
    act(() => result.current.shut())
    expect(result.current.share).toBe(SPLIT.share)
    act(() => result.current.setShare(0.7))
    act(() => result.current.shut())
    expect(result.current.share).toBe(0.7)
  })

  it('stepping the study follows the list, even back onto the ayah that was tapped', () => {
    const onPlace = vi.fn()
    const { result, rerender } = mount({ surah: 2, ayah: 5 }, onPlace)
    act(() => result.current.open(5))
    expect(result.current.tapped).toBe(5)
    act(() => result.current.sheet.onNext())
    expect(onPlace).toHaveBeenLastCalledWith({ surah: 2, ayah: 6 })
    expect(result.current.tapped).toBeNull()
    rerender({ place: { surah: 2, ayah: 6 }, onPlace })
    act(() => result.current.sheet.onPrev())
    expect(onPlace).toHaveBeenLastCalledWith({ surah: 2, ayah: 5 })
    expect(result.current.tapped).toBeNull()
  })

  it('closing the study notes where the list was looking, and anything that opens or moves elsewhere forgets it', () => {
    const onPlace = vi.fn()
    const { result, rerender } = mount({ surah: 2, ayah: 31 }, onPlace)
    expect(result.current.resting).toBeNull()
    result.current.list.current.scrollTop = 3040          // 40px into row 31 (rows are 100px, row n starts at (n-1)*100)
    act(() => result.current.shut())
    expect(result.current.resting).toEqual({ ayah: 31, into: 40 })
    rerender({ place: { surah: 2, ayah: null }, onPlace })
    act(() => result.current.open(7))
    expect(result.current.resting).toBeNull()
    rerender({ place: { surah: 2, ayah: 7 }, onPlace })
    act(() => result.current.shut())
    expect(result.current.resting).not.toBeNull()
    act(() => result.current.changeSurah(3))
    expect(result.current.resting).toBeNull()
  })
})
