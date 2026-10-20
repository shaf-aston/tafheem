import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import WordGrid from './WordGrid'

const word = (id, category, image = '') => ({ id, english: id, arabic: `ع${id}`, transliteration: id, category, image })

describe('WordGrid', () => {
  it('draws every word under its heading, a picture where there is one', () => {
    const html = renderToStaticMarkup(<WordGrid words={[
      word('bread', 'food', 'words/bread.jpg'), word('rice', 'food'), word('salt', 'food'),
      word('cup', 'home'), word('plate', 'home'), word('spoon', 'home'),
    ]} />)
    expect(html.match(/<h4/g)).toHaveLength(2)
    expect(html.match(/<li/g)).toHaveLength(6)
    expect(html.match(/<img/g)).toHaveLength(1)
    expect(html).toContain('words/bread.jpg')
  })
})
