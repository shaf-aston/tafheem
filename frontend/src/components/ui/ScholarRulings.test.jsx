// Static markup, like VerbFormTag.test.jsx: no jsdom here.
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import ScholarRulings from './ScholarRulings'

const ilal = {
  kind: 'ilal', label: "Asked of Abu Hatim or Abu Zur'a", scholar: 'أبو حاتم', chapter: 'علل الصلاة',
  quote: 'قال أبي: هذا حديث منكر، إلا أن يكون عن فلان.', source: "Ibn Abi Hatim, 'Ilal al-Hadith", page: 'v2 p. 337',
}
const chapterOnly = { kind: 'nasikh_chapter', label: 'In a book of abrogation', scholar: 'ابن شاهين', chapter: 'ذكر زيارة القبور', quote: '', source: 'Ibn Shahin', page: 'no. 5' }

describe('ScholarRulings', () => {
  it('prints nothing for a hadith no book speaks of', () => {
    expect(renderToStaticMarkup(<ScholarRulings rulings={[]} />)).toBe('')
  })

  it('quotes the whole sentence, its qualifier included, with the book and page, under a header that says possible', () => {
    const html = renderToStaticMarkup(<ScholarRulings rulings={[ilal]} />)
    expect(html).toContain('Possible')
    expect(html).toContain('قال أبي: هذا حديث منكر، إلا أن يكون عن فلان.')
    expect(html).toContain("Ibn Abi Hatim, &#x27;Ilal al-Hadith, v2 p. 337")
  })

  it('shows the chapter heading alone where the book adds no remark', () => {
    const html = renderToStaticMarkup(<ScholarRulings rulings={[chapterOnly]} />)
    expect(html).toContain('ذكر زيارة القبور')
    expect(html).toContain('Ibn Shahin, no. 5')
  })
})
