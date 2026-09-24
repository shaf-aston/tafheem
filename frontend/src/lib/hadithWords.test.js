import { describe, expect, it } from 'vitest'

import { hadithKey, narrated, printedBy, saying } from './hadithWords'

describe('saying', () => {
  it('marks a quoted stretch as said and the rest as told', () => {
    expect(saying('The Prophet said, "Pray as you have seen me pray." Then he left.')).toEqual([
      { kind: 'told', text: 'The Prophet said,' },
      { kind: 'said', text: 'Pray as you have seen me pray.' },
      { kind: 'told', text: 'Then he left.' },
    ])
  })

  it('reads the Arabic mark with its direction marks around it', () => {
    expect(saying('قَالَ ‏"‏ إِنَّ أَحَدَكُمْ ‏"‏ .')).toEqual([
      { kind: 'told', text: 'قَالَ' },
      { kind: 'said', text: 'إِنَّ أَحَدَكُمْ' },
      { kind: 'told', text: '.' },
    ])
  })

  it('claims nothing when the book marked nothing', () => {
    expect(saying('The Last Hour would not come until fire emits from the Hijaz')).toEqual([
      { kind: 'plain', text: 'The Last Hour would not come until fire emits from the Hijaz' },
    ])
  })

  it('keeps several sayings apart', () => {
    expect(saying('He said "one" then "two"').filter((s) => s.kind === 'said')).toEqual([
      { kind: 'said', text: 'one' },
      { kind: 'said', text: 'two' },
    ])
  })

  it('has nothing to say about nothing', () => {
    expect(saying('')).toEqual([])
    expect(saying(null)).toEqual([])
  })
})

describe('narrated', () => {
  it('splits the narrator off at the colon the books put there', () => {
    expect(narrated('Narrated `Abdullah bin `Umar:Allah\'s Messenger said, "..."')).toEqual({
      narrator: 'Narrated `Abdullah bin `Umar:',
      body: 'Allah\'s Messenger said, "..."',
    })
  })

  it('leaves a hadith with no narrator line whole', () => {
    expect(narrated('The Hour will not come until the sun rises from the west')).toEqual({
      narrator: '',
      body: 'The Hour will not come until the sun rises from the west',
    })
  })

  it('does not take a colon deep inside the words for a narrator', () => {
    const long = `${'He reported at length '.repeat(12)}: and then`
    expect(narrated(long).narrator).toBe('')
  })
})

describe('hadithKey', () => {
  it('names a hadith reference and nothing else', () => {
    expect(hadithKey({ hadith: 'muslim', number: 2902 })).toBe('muslim:2902')
    expect(hadithKey({ hadith: 'muslim', number: 157, part: 'c' })).toBe('muslim:157c')
    expect(hadithKey({ quran: '2:255' })).toBe('')
    expect(hadithKey(null)).toBe('')
  })
})

describe('printedBy', () => {
  const event = {
    refs: [{ hadith: 'muslim', number: 2920, part: 'a' }],
    steps: [
      { id: 'one', refs: [{ hadith: 'muslim', number: 2920, part: 'a' }, { hadith: 'bukhari', number: 81 }] },
      { id: 'two', refs: [{ hadith: 'bukhari', number: 81 }], steps: [{ id: 'deep', refs: [{ quran: '2:255' }] }] },
    ],
  }

  it('gives each hadith to the first place that cites it', () => {
    const prints = printedBy(event)
    expect([...prints.get('')]).toEqual(['muslim:2920a'])
    expect([...prints.get('one')]).toEqual(['bukhari:81'])
    expect([...prints.get('two')]).toEqual([])
  })

  it('reaches the moments inside a step, and keeps out what is not a hadith', () => {
    expect([...printedBy(event).get('deep')]).toEqual([])
  })

  it('has an answer for an event with nothing in it', () => {
    expect([...printedBy({}).get('')]).toEqual([])
  })
})
