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

describe('useSurahPlace: closing the study', () => {
  beforeEach(phone)

  it('keeps the reader on the same row when the layout change moves the list', () => {
    const onPlace = vi.fn()
    const { result, rerender } = mount({ surah: 2, ayah: 31 }, onPlace)
    expect(result.current.stacked).toBe(true)
    act(() => result.current.shut())
    expect(onPlace).toHaveBeenCalledWith({ surah: 2, ayah: null })
    // The browser put the list somewhere else while the study went (here: back to the start).
    result.current.list.current.scrollTop = 0
    rerender({ place: { surah: 2, ayah: null }, onPlace })
    expect(result.current.stacked).toBe(false)
    expect(result.current.list.current.scrollTop).toBe(3000)
    expect(result.current.here).toBe(31)
  })

  it('leaves the list alone when the close did not disturb it', () => {
    const onPlace = vi.fn()
    const { result, rerender } = mount({ surah: 2, ayah: 31 }, onPlace)
    const list = result.current.list.current
    list.scrollTop = 3040   // part-way down a row: a restore would snap it to the row's top
    act(() => result.current.shut())
    rerender({ place: { surah: 2, ayah: null }, onPlace })
    expect(list.scrollTop).toBe(3040)
  })

  it('does not restore on its own later: only a close asks for it', () => {
    const onPlace = vi.fn()
    const { result, rerender } = mount({ surah: 2, ayah: null }, onPlace)
    result.current.list.current.scrollTop = 800
    rerender({ place: { surah: 2, ayah: null }, onPlace })
    expect(result.current.list.current.scrollTop).toBe(800)
  })

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
})
