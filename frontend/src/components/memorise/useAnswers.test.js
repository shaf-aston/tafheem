// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest'
import { act, renderHook } from '@testing-library/react'

import { gapsScope, useAnswers } from './useAnswers'

const at = (pageNumber, more = {}) => gapsScope({ bookId: 'quran', part: 4, pageNumber, way: 'type', difficulty: 'some', deal: 1, pinned: null, ...more })
const open = (scope) => renderHook(({ scope: now }) => useAnswers(now), { initialProps: { scope } })

describe('gapsScope', () => {
  it('names the page and every setting that moves a gap, and nothing else', () => {
    expect(at(0)).toBe(at(0))
    for (const other of [at(1), at(0, { way: 'pick' }), at(0, { difficulty: 'most' }), at(0, { deal: 2 }), at(0, { pinned: 5 }), at(0, { part: 5 })]) {
      expect(other).not.toBe(at(0))
    }
  })
})

describe('useAnswers', () => {
  it('finds a page as it was left after turning away and back', () => {
    const view = open(at(0))
    act(() => { view.result.current.setAnswers({ '0:1': 'x' }); view.result.current.setChecked(true) })
    view.rerender({ scope: at(1) })
    expect(view.result.current).toMatchObject({ answers: {}, checked: false })
    view.rerender({ scope: at(0) })
    expect(view.result.current).toMatchObject({ answers: { '0:1': 'x' }, checked: true })
  })

  it('keeps each page apart, and takes updaters as well as values', () => {
    const view = open(at(0))
    act(() => view.result.current.setAnswers((was) => ({ ...was, a: '1' })))
    act(() => view.result.current.setAnswers((was) => ({ ...was, b: '2' })))
    view.rerender({ scope: at(1) })
    act(() => view.result.current.setAnswers({ c: '3' }))
    view.rerender({ scope: at(0) })
    expect(view.result.current.answers).toEqual({ a: '1', b: '2' })
  })

  it('"Try again" empties this page only: answers, marking and shown words', () => {
    const view = open(at(0))
    act(() => {
      view.result.current.setAnswers({ '0:1': 'x' })
      view.result.current.setChecked(true)
      view.result.current.setShown(new Set([2]))
    })
    view.rerender({ scope: at(1) })
    act(() => view.result.current.setAnswers({ '0:2': 'y' }))
    act(() => view.result.current.fresh())
    expect(view.result.current).toMatchObject({ answers: {}, checked: false })
    expect(view.result.current.shown.size).toBe(0)
    view.rerender({ scope: at(0) })
    expect(view.result.current).toMatchObject({ answers: { '0:1': 'x' }, checked: true })
    expect(view.result.current.shown.has(2)).toBe(true)
  })
})
