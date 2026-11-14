import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderToStaticMarkup } from 'react-dom/server'
import { beforeEach, describe, expect, it } from 'vitest'
import { forgetSeen, markSeen } from '../../../lib/colloquial/seen'
import { DialectList, TopicList, UnitList } from './Lists'

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

describe('what this device has opened', () => {
  beforeEach(() => forgetSeen())
  const unit = { ...talk(1), lessons: [{ ...topic(4), lesson: 'lesson-01' }, { ...topic(4), lesson: 'lesson-02', title: 'second' }] }
  const dialect = { key: 'fusha', label: 'Fusha', where: 'Everywhere', units: [unit], countries: [], cities: [] }

  it('a unit says how many of its topics were opened, and a topic says it was', () => {
    markSeen('fusha/unit-01/lesson-02')
    expect(renderToStaticMarkup(<UnitList dialect={dialect} go={() => {}} />)).toContain('1 of 2 topics seen')
    const topics = renderToStaticMarkup(<QueryClientProvider client={new QueryClient()}><TopicList dialect={dialect} unit={unit} go={() => {}} /></QueryClientProvider>)
    expect(topics).toContain('Topic 2 · Seen')
    expect(topics).not.toContain('Topic 1 · Seen')
  })

  it('the dialect list offers the way back to the last topic, and nothing before one was opened', () => {
    const none = renderToStaticMarkup(<DialectList dialects={[dialect]} go={() => {}} />)
    expect(none).not.toContain('Continue where you left off')
    markSeen('fusha/unit-01/lesson-02')
    const some = renderToStaticMarkup(<DialectList dialects={[dialect]} go={() => {}} />)
    expect(some).toContain('Continue where you left off')
    expect(some).toContain('second')
    expect(some).toContain('Fusha · Unit 1')
  })
})

describe('a unit’s topic cards, as a new learner reads them', () => {
  const unit = { ...talk(1), lessons: [{ ...topic(14), lesson: 'lesson-01', title: 'Greetings' }] }
  const dialect = { key: 'fusha', label: 'Fusha', where: 'Everywhere', units: [unit], countries: [], cities: [] }
  const html = () => renderToStaticMarkup(<QueryClientProvider client={new QueryClient()}><TopicList dialect={dialect} unit={unit} go={() => {}} /></QueryClientProvider>)

  it('says what a topic holds, as its Words half does: a count, and that there is practice', () => {
    expect(html()).toContain('14 phrases · practice')
    expect(html()).toContain('3 to learn')
  })

  it('names each half by what it shows (no hidden name to differ), and the Words half says whose words they are', () => {
    const buttons = html().match(/<button[^>]*>/g)
    expect(buttons.length).toBeGreaterThanOrEqual(2)
    for (const b of buttons) expect(b).not.toContain('aria-label')
    expect(html()).toMatch(/<span class="sr-only">,\s*(<!-- -->)?\s*Greetings<\/span>/)
  })
})
