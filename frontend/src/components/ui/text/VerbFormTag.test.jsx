// Rendered with renderToStaticMarkup: no jsdom is installed here, and a static
// HTML string is enough to check the branches without a new dependency.
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import VerbFormTag from './VerbFormTag'

const lane = { key: 'lane', label: "Lane's Arabic-English Lexicon", confidence: 'verified' }
const wiktionary = { key: 'wiktionary', label: 'Wiktionary', confidence: 'verified' }

describe('VerbFormTag', () => {
  it('no readings: the never-guess placeholder line, nothing else', () => {
    const html = renderToStaticMarkup(<VerbFormTag readings={[]} />)
    expect(html).toContain('No dictionary here records this verb')
  })

  it('one reading, one source: label and its badge', () => {
    const html = renderToStaticMarkup(
      <VerbFormTag readings={[{ label: 'كَتَبَ · باب نَصَرَ يَنْصُرُ', sources: [wiktionary] }]} />
    )
    expect(html).toContain('كَتَبَ · باب نَصَرَ يَنْصُرُ')
    expect(html).toContain('Wiktionary')
    expect(html).not.toContain('Lane')
  })

  it('one reading, two sources: both badges on the same line', () => {
    const html = renderToStaticMarkup(
      <VerbFormTag readings={[{ label: 'كَتَبَ · باب نَصَرَ يَنْصُرُ', sources: [lane, wiktionary] }]} />
    )
    expect(html).toContain('Lane')
    expect(html).toContain('Wiktionary')
  })

  it('two readings: both labels render', () => {
    const html = renderToStaticMarkup(
      <VerbFormTag readings={[
        { label: 'زَقَمَ · باب نَصَرَ يَنْصُرُ', sources: [lane] },
        { label: 'زَقَمَ · باب ضَرَبَ يَضْرِبُ', sources: [wiktionary] },
      ]} />
    )
    expect(html).toContain('زَقَمَ · باب نَصَرَ يَنْصُرُ')
    expect(html).toContain('زَقَمَ · باب ضَرَبَ يَضْرِبُ')
  })
})
