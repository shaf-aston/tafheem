import { describe, expect, it } from 'vitest'
import spine from '../../../../backend/data/colloquial/spine.json'
import { pictureBoards } from './wordPictures'

const topic = (title) => spine.units.flatMap((u) => u.lessons).find((l) => l.title === title)
const wordsOf = (ids) => ids.map((id) => ({ id, english: id, arabic: `ع${id}` }))
const inside = (b) => b.spots.every(({ x, y }) => x >= b.view[0] && y >= b.view[1] && x <= b.view[0] + b.view[2] && y <= b.view[1] + b.view[3])

describe('pictureBoards', () => {
  it('puts the body topic on a face, a figure and a hand, every spot a real word of it', () => {
    const boards = pictureBoards(wordsOf(topic('The Body, Head to Toe').words))
    expect(boards.map((b) => b.id)).toEqual(['face', 'figure', 'hand'])
    expect(boards.flatMap((b) => b.spots).length).toBe(38)
    expect(boards.every(inside)).toBe(true)
  })

  it('puts countries and their people on the same dot, on three maps', () => {
    const boards = pictureBoards(wordsOf(topic('Countries and Nationalities').words))
    expect(boards.map((b) => b.id)).toEqual(['levant', 'gulf', 'africa'])
    const syria = boards[0].spots.find((s) => s.key === 'SY')
    expect(syria.words.map((w) => w.id)).toEqual(['syria', 'syrian'])
    expect(boards.every(inside)).toBe(true)
  })

  it('gives a topic with no drawing no boards', () => {
    expect(pictureBoards(wordsOf(['bread', 'rice', 'salt', 'head']))).toEqual([])
  })
})
