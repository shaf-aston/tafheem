import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { CountryIcons, CountryMap } from './CountryMap'

describe('CountryMap', () => {
  it('draws its countries in the hue, a dot per city, and faint neighbours', () => {
    const html = renderToStaticMarkup(<CountryMap codes={['LB']} cities={[{ name: 'Beirut', at: [35.5, 33.89] }]} hue="#c80" />)
    expect(html.match(/stroke="#c80"/g)).toHaveLength(1)
    expect(html.match(/<circle/g)).toHaveLength(1)
    // Syria sits beside Lebanon, so it is drawn as a neighbour.
    expect(html.match(/var\(--surface-hi\)/g).length).toBeGreaterThan(1)
  })

  it('draws nothing for codes it has no outline for', () => {
    expect(renderToStaticMarkup(<CountryMap codes={['ZZ']} hue="#c80" />)).toBe('')
  })
})

describe('CountryIcons', () => {
  it('names each country beside its outline', () => {
    const html = renderToStaticMarkup(<CountryIcons codes={['KW', 'QA']} hue="#c80" />)
    expect(html).toContain('Kuwait')
    expect(html).toContain('Qatar')
    expect(html.match(/<svg/g)).toHaveLength(2)
  })

  it('past the most, says how many instead', () => {
    const html = renderToStaticMarkup(<CountryIcons codes={['EG', 'SY', 'LB', 'IQ', 'YE']} hue="#c80" />)
    expect(html).toContain('5 countries')
    expect(html).not.toContain('<svg')
  })
})
