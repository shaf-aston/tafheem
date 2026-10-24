import { describe, expect, it } from 'vitest'

import { exampleMatches } from './exampleSearch'

// A real card: the first example the Nahw tab shows, and the topic it is
// labelled with in topics.json.
const example = {
  sentence: 'جَاءَ الَّذِيْ أَبُوْهُ عَالِمٌ',
  translation: 'The one whose father is a scholar came.',
  topic: 'verbal',
}
const topic = { key: 'verbal', ar: 'الْجُمْلَةُ الْفِعْلِيَّةُ', en: 'Verbal sentence' }

const finds = (typed) => exampleMatches(example, topic, typed)

describe('finding a worked example', () => {
  it('finds it by the topic on its own card, typed with no vowel marks', () => {
    expect(finds('الجملة الفعلية')).toBe(true)
  })

  it('finds it by that same topic pasted with every mark on it', () => {
    expect(finds(topic.ar)).toBe(true)
  })

  it('finds it by the topic in English', () => {
    expect(finds('verbal')).toBe(true)
  })

  it('finds it by a word of the sentence typed the way a keyboard types it', () => {
    expect(finds('عالم')).toBe(true)
    // Written أَبُوْهُ with a hamza the reader will not reach for.
    expect(finds('ابوه')).toBe(true)
  })

  it('finds it by its English, whatever the capitals', () => {
    expect(finds('SCHOLAR')).toBe(true)
  })

  it('matches everything while the box is empty', () => {
    expect(finds('')).toBe(true)
    expect(finds('   ')).toBe(true)
  })

  it('still finds nothing when the letters are not there', () => {
    expect(finds('الفعل المضارع')).toBe(false)
    expect(finds('donkey')).toBe(false)
  })

  it('keeps the example findable by its own words when its topic is unknown', () => {
    expect(exampleMatches(example, undefined, 'عالم')).toBe(true)
    expect(exampleMatches(example, undefined, 'الجملة الفعلية')).toBe(false)
  })
})
