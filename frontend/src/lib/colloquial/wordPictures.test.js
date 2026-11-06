import { describe, expect, it } from 'vitest'
import spine from '../../../../backend/data/colloquial/spine.json'
import { pictureBoards } from './wordPictures'

const topic = (title) => spine.units.flatMap((u) => u.lessons).find((l) => l.title === title)
const wordsOf = (ids) => ids.map((id) => ({ id, english: id, arabic: `ع${id}` }))
const inside = (b) => b.spots.every(({ x, y }) => x >= b.view[0] && y >= b.view[1] && x <= b.view[0] + b.view[2] && y <= b.view[1] + b.view[3])

describe('pictureBoards', () => {
  it('puts the body topic on a face, a figure, a hand and a leg, every spot a real word of it', () => {
    const boards = pictureBoards(wordsOf(topic('The Body, Head to Toe').words))
    expect(boards.map((b) => b.id)).toEqual(['face', 'figure', 'hand', 'leg'])
    expect(boards.flatMap((b) => b.spots).length).toBe(44)
    expect(boards.every(inside)).toBe(true)
  })

  it('dresses a figure for the clothes topic, and the region\'s clothes on three more', () => {
    const boards = pictureBoards(wordsOf(topic('Clothes and Accessories').words))
    expect(boards.map((b) => b.id)).toEqual(['outfit', 'traditional'])
    // Jeans are trousers: one place answers both.
    expect(boards[0].spots.find((s) => s.key === 'trousers').words.map((w) => w.id)).toEqual(['trousers', 'jeans'])
  })

  it('lays a table, and grows a plant', () => {
    expect(pictureBoards(wordsOf(topic('Kitchen and Tableware').words)).map((b) => b.id)).toContain('table')
    expect(pictureBoards(wordsOf(topic('Plants and Trees').words)).map((b) => b.id)).toEqual(['plant'])
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

  it("draws the family on a tree, the sister's husband answering 'husband' too", () => {
    const [tree] = pictureBoards(wordsOf(topic('Family').words))
    expect(tree.id).toBe('family')
    const bil = tree.spots.find((s) => s.key === 'brother-in-law')
    expect(bil.words.map((w) => w.id)).toEqual(['brother-in-law', 'husband'])
  })

  it('lays a grid board out with only the panels taught, each keeping its place in the set', () => {
    const [week] = pictureBoards(wordsOf(['friday', 'saturday', 'sunday']))
    expect(week.id).toBe('week')
    expect(week.spots.map((s) => [s.key, s.order])).toEqual([['sunday', 1], ['friday', 6], ['saturday', 7]])
    expect(week.view).toEqual([0, 0, 150, 72])
  })

  it('puts "in" and "inside" on one panel', () => {
    const [where] = pictureBoards(wordsOf(['in', 'inside', 'on', 'under']))
    expect(where.spots[1].words.map((w) => w.id)).toEqual(['in', 'inside'])
  })

  it("keeps every spot of every topic's boards inside its drawing, one spot per word", () => {
    for (const lesson of spine.units.flatMap((u) => u.lessons)) {
      for (const board of pictureBoards(wordsOf(lesson.words ?? []))) {
        expect(inside(board), `${lesson.title}: ${board.id}`).toBe(true)
        const ids = board.spots.flatMap((s) => s.words.map((w) => w.id))
        expect(new Set(ids).size).toBe(ids.length)
        // Every dot is a finger-sized target: no two dots on top of each other (a map is tapped by country, not by dot).
        const dots = board.art === 'map' ? [] : board.spots.filter((x) => !x.area)
        const reach = board.view[2] / 30 * 2
        for (const [i, a] of dots.entries()) {
          for (const b of dots.slice(i + 1)) {
            expect(Math.hypot(a.x - b.x, a.y - b.y), `${lesson.title}: ${board.id}: ${a.key} / ${b.key}`).toBeGreaterThanOrEqual(reach)
          }
        }
      }
    }
  })
})
