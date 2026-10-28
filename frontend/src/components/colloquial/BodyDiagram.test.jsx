import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import BodyDiagram from './BodyDiagram'

const word = (id, english, arabic) => ({ id, english, arabic, transliteration: id, category: 'body' })

describe('BodyDiagram', () => {
  it('draws a hotspot for each word it knows a place for', () => {
    const html = renderToStaticMarkup(<BodyDiagram words={[
      word('knee', 'knee', 'ركبة'), word('x', 'nonsense', 'ح'),
    ]} />)
    expect(html.match(/role="button"/g)).toHaveLength(1)
  })

  it('draws nothing when no word has a known place', () => {
    expect(renderToStaticMarkup(<BodyDiagram words={[word('x', 'nonsense', 'ح')]} />)).toBe('')
  })
})
