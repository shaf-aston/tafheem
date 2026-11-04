import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { UnitList } from './Lists'

const topic = (phrases) => ({ lesson: 'lesson-01', title: 't', written: true, phrases, words: 3 })
const talk = (n) => ({ unit: `unit-0${n}`, title: `Talk ${n}`, written: true, lessons: [topic(4)], cover: null, samples: [], words: 0 })
const words = (n) => ({
  unit: `unit-0${n}`, title: `Words ${n}`, written: true, lessons: [topic(0)], cover: null, words: 12,
  samples: [{ arabic: 'أَحْمَر / حَمْرَاء', english: 'red', image: 'emoji/1f534.svg' }],
})
const list = (units) => renderToStaticMarkup(<UnitList dialect={{ key: 'fusha', units }} go={() => {}} />)

describe('UnitList', () => {
  it('puts talk units and word units on two headed shelves', () => {
    const html = list([talk(1), talk(2), words(3)])
    expect(html.match(/<h2/g)).toHaveLength(2)
    expect(html).toContain('Units 1–2')
    expect(html).toContain('Units 3–3')
    expect(html.indexOf('Talk 2')).toBeLessThan(html.indexOf('Words 3'))
  })

  it('shows a word unit by its sample words and size, the first form only', () => {
    const html = list([talk(1), words(2)])
    expect(html).toContain('12 words')
    expect(html).toContain('أَحْمَر<')
    expect(html).not.toContain('حَمْرَاء')
  })

  it('draws one unheaded grid when a dialect has one kind of unit', () => {
    expect(list([talk(1), talk(2)])).not.toContain('<h2')
  })
})
