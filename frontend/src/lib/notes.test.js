import { describe, expect, it } from 'vitest'

import { cardsOf, gapped, markedIn, parseMarked, rolesUsed, runOf, stripMarks } from './notes'

describe('reading the marks', () => {
  it('splits a line into plain runs and marked pieces, in order', () => {
    expect(parseMarked('الحال {{ruling|منصوب}} أبدا')).toEqual([
      { text: 'الحال ', role: null },
      { text: 'منصوب', role: 'ruling' },
      { text: ' أبدا', role: null },
    ])
  })

  it('reads a line with no marks as one plain run, and an empty line as nothing', () => {
    expect(parseMarked('بلا علامة')).toEqual([{ text: 'بلا علامة', role: null }])
    expect(parseMarked('')).toEqual([])
    expect(parseMarked(undefined)).toEqual([])
  })

  it('gives the teacher\'s own wording back with the marks taken off', () => {
    expect(stripMarks('{{term|الحال}} {{ruling|منصوب}}')).toBe('الحال منصوب')
  })
})

describe('gaps', () => {
  it('blanks the marked piece, not an earlier plain copy of the same words', () => {
    const [piece] = markedIn({ id: 'b', kind: 'rule', page: 0, ar: 'نكرة ثم {{ruling|نكرة}}' })
    expect(gapped(piece)).toBe('نكرة ثم _____')
  })

  it('keeps a piece marked twice in one line as two pieces, each gapping only itself', () => {
    const pieces = markedIn({ id: 'b', kind: 'rule', page: 0, ar: '{{term|حال}} و{{term|حال}}' })
    expect(pieces).toHaveLength(2)
    expect(pieces.map((p) => gapped(p))).toEqual(['_____ وحال', 'حال و_____'])
  })

  it('reads a block the way the API sends it, with absent fields as null', () => {
    const block = { id: 'b', kind: 'rule', page: 0, ar: '{{term|حال}}', en: null, items: null, rows: null, labels: null }
    expect(markedIn(block)).toHaveLength(1)
    expect(cardsOf({ blocks: [block] }, ['term', 'label'])).toHaveLength(1)
  })

  it('finds marks inside list lines and table cells too', () => {
    const block = { id: 'b', kind: 'table', page: 0, columns: ['a'], rows: [['{{term|ظرف}}']], items: ['{{ruling|منصوب}}'] }
    expect(markedIn(block).map((p) => p.field).sort()).toEqual(['items.0', 'rows.0.0'])
  })
})

const topic = {
  blocks: [
    { id: 'r', kind: 'rule', page: 0, ar: 'الحال {{ruling|منصوب}} وصاحبه {{term|ذو الحال}}' },
    {
      id: 't', kind: 'table', page: 1, caption: 'مواضع', columns: ['الموضع', 'مثال'], answer_col: 0,
      rows: [['{{term|جملة إسمية}}', 'جاء زيد والشمس طالعة'], ['{{term|جملة إسمية}}', 'جاء زيد والشمس طالعة']],
    },
    { id: 'e', kind: 'example', page: 2, ar: 'جاء زيد راكبا', labels: [{ word: 'راكبا', label: 'حال' }] },
  ],
}

describe('cards', () => {
  it('makes a card per chosen role, in page order', () => {
    const cards = cardsOf(topic, ['ruling'])
    expect(cards[0]).toMatchObject({ kind: 'piece', back: 'منصوب', front: 'الحال _____ وصاحبه ذو الحال' })
  })

  it('leaves out roles not chosen, and label cards unless labels are chosen', () => {
    const kinds = cardsOf(topic, ['ruling']).map((c) => c.kind)
    expect(kinds).not.toContain('label')
    expect(cardsOf(topic, ['label']).filter((c) => c.kind === 'label')).toEqual([
      expect.objectContaining({ front: 'جاء زيد راكبا · راكبا', back: 'حال' }),
    ])
  })

  it('asks a table by its answer column, with no second card for a mark in that column', () => {
    const rows = cardsOf(topic, ['term']).filter((c) => c.blockId === 't')
    expect(rows.every((c) => c.kind === 'row')).toBe(true)
    expect(rows[0]).toMatchObject({ front: 'مواضع · جاء زيد والشمس طالعة', back: 'جملة إسمية' })
  })

  it('keeps two identical table rows as two cards', () => {
    expect(cardsOf(topic, []).filter((c) => c.kind === 'row')).toHaveLength(2)
  })

  it('gives no cards for a topic with nothing in it', () => {
    expect(cardsOf({ blocks: [] }, ['term'])).toEqual([])
    expect(cardsOf(undefined, ['term'])).toEqual([])
  })

  it('says which roles a topic uses, so a switch that would hide nothing is not offered', () => {
    expect([...rolesUsed(topic)].sort()).toEqual(['ruling', 'term'])
  })
})

describe('runs', () => {
  const cards = Array.from({ length: 5 }, (_, i) => i)
  it('takes a run from a starting point, and a short last run when fewer are left', () => {
    expect(runOf(cards, 0, 2)).toEqual([0, 1])
    expect(runOf(cards, 4, 2)).toEqual([4])
    expect(runOf(cards, 5, 2)).toEqual([])
  })
})
