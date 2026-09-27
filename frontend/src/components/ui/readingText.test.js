/**
 * What a reader can select out of a line of Arabic is the Arabic, and the
 * Qur'an's own spelling asks for the face cut for its marks. Rendered to real
 * markup, the way the page receives it.
 */
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { isQuranic } from '../../lib/arabicText'
import ArabicText from './ArabicText'
import GlossWord from './GlossWord'
import Tooltip from './Tooltip'

// The text a selection of this markup would copy: every text node, no attributes.
const selectable = (html) => html.replace(/<[^>]*>/g, '')

describe('a word with its English gloss', () => {
  const html = renderToStaticMarkup(
    h(ArabicText, { as: 'div' },
      h(GlossWord, { gloss: 'Those' }, 'أُو۟لَٰٓئِكَ'), ' ',
      h(GlossWord, { gloss: 'guided', lit: true }, 'هَدَى')))

  it('copies as the Arabic alone', () => {
    expect(selectable(html)).toBe('أُو۟لَٰٓئِكَ هَدَى')
  })

  it('still carries the English for the page to draw and a screen reader to say', () => {
    expect(html).toContain('data-gloss="Those"')
    expect(html).toContain('aria-description="Those"')
    expect(html).toContain('gloss-word-lit')
  })

  it('draws no gloss where there is none', () => {
    expect(renderToStaticMarkup(h(GlossWord, null, 'هَدَى'))).not.toContain('data-gloss')
  })
})

describe('the Qur\'an in its own spelling', () => {
  it('is known by marks only the mushaf uses', () => {
    expect(isQuranic('أُو۟لَٰٓئِكَ ٱلَّذِينَ هَدَى ٱللَّهُ ۖ')).toBe(true)
    expect(isQuranic('ذَهَبَ الطَّالِبُ إِلَى الْمَدْرَسَةِ')).toBe(false)
    expect(isQuranic(undefined)).toBe(false)
  })

  it('is flagged for its own face, however deep the words sit', () => {
    const ayah = renderToStaticMarkup(h(ArabicText, { as: 'div' }, h(GlossWord, null, 'ٱللَّهُ')))
    expect(ayah).toMatch(/^<div[^>]*data-script="quran"/)
  })

  it('leaves everyday Arabic in the reading face', () => {
    const plain = renderToStaticMarkup(h(ArabicText, null, 'ذَهَبَ الطَّالِبُ إِلَى الْمَدْرَسَةِ'))
    expect(plain).not.toContain('data-script')
  })
})

describe('a tooltip', () => {
  it('holds its note for the page to draw, not as text to copy', () => {
    const html = renderToStaticMarkup(h(Tooltip, { text: 'Treebank\'s wording, unchecked.' }, 'صِلَةٌ'))
    expect(selectable(html)).toBe('صِلَةٌ')
    expect(html).toContain('data-tip="Treebank&#x27;s wording, unchecked."')
  })
})
