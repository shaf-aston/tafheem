import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

import worlds from '../../config/worlds.json'
import { makeRandom } from '../quiz/quiz'
import { phrasesOf, prayerCards } from './prayerLesson'

// The world as /api/grow/worlds/prayer serves its paths: routers/grow.py reads the same files, in world.json's order,
// and fills each ruling's book and author in from sources.json.
const FOLDER = new URL('../../../../backend/data/grow/', import.meta.url)
const read = (file) => JSON.parse(readFileSync(new URL(file, FOLDER), 'utf8'))
const { sources } = read('sources.json')
const served = (step) => (step.ruling ? { ...step, ruling: { ...sources[step.ruling.source], ...step.ruling } } : step)
const pathOf = (name) => {
  const path = read(`worlds/prayer/paths/${name}.json`)
  return { ...path, steps: path.steps.map(served) }
}
const world = { paths: read('worlds/prayer/world.json').paths.map(pathOf) }
const phrases = phrasesOf(world)

describe('phrasesOf', () => {
  it('takes every step with words to say, from wudu to the adhkar, and leaves postures and surahs out', () => {
    expect(phrases[0].id).toBe('wudu-dua')
    expect(phrases.map((p) => p.id)).toEqual(expect.arrayContaining(['takbir', 'thana', 'tashahhud', 'taslim', 'tasbih']))
    for (const phrase of phrases) expect(phrase.arabic && phrase.meaning).toBeTruthy()
  })

  it('counts words said twice once: the takbir, again in the 33s', () => {
    expect(phrases.map((p) => p.id)).not.toContain('takbir-33')
  })

  it('is what the world in worlds.json counts to', () => {
    const { stages } = worlds.worlds.find((one) => one.id === 'prayer')
    expect(stages.at(-1)).toBe(phrases.length)
  })
})

describe('prayerCards', () => {
  const byId = (id) => phrases.find((p) => p.id === id)

  it('teaches a new phrase with its source, then asks its meaning and its missing word', () => {
    const cards = prayerCards({ fresh: [byId('thana')], reviews: [] }, phrases, makeRandom(1))
    expect(cards.map((c) => c.kind)).toEqual(['teach', 'meaning', 'gap'])
    expect(cards[0].note).toContain('al-Quduri')
    expect(new Set(cards[1].question.options.map((o) => o.id)).size).toBe(4)
    expect(cards[1].record).toMatchObject({ module: 'prayer', item: 'thana' })
    expect(cards[2].gap.options.map((o) => o.text)).toContain(cards[2].gap.answer)
  })

  it('asks a one-word phrase only its meaning: a gap would blank the whole of it', () => {
    const cards = prayerCards({ fresh: [byId('amin')], reviews: [] }, phrases, makeRandom(2))
    expect(cards.map((c) => c.kind)).toEqual(['teach', 'meaning'])
  })

  it('asks a review one way only', () => {
    const cards = prayerCards({ fresh: [], reviews: [byId('tashahhud')] }, phrases, makeRandom(3))
    expect(cards).toHaveLength(1)
    expect(cards[0].tag).toBe('Review')
  })
})
