import { describe, expect, it } from 'vitest'

import { lookingAt, rowAt, showRow } from './surahRows'

// Rows 100px tall: row n starts at (n - 1) * 100.
const list = (scrollTop = 0, rows = 20) => ({ scrollTop, children: Array.from({ length: rows }, (_, i) => ({ offsetTop: i * 100 })) })

describe('surahRows', () => {
  it('rowAt is the row at the top of the list', () => {
    expect(rowAt(list(0))).toBe(1)
    expect(rowAt(list(950))).toBe(10)
    expect(rowAt(list(1000))).toBe(11)
  })

  it('lookingAt is that row and how far down it, and showRow puts exactly that back', () => {
    const at = list(1240)
    expect(lookingAt(at)).toEqual({ ayah: 13, into: 40 })
    const again = list(0)
    showRow(again, 13, 40)
    expect(again.scrollTop).toBe(1240)
    showRow(again, 5)
    expect(again.scrollTop).toBe(400)
  })

  it('a row that is not there moves nothing', () => {
    const at = list(300)
    showRow(at, 99, 10)
    expect(at.scrollTop).toBe(300)
  })
})
