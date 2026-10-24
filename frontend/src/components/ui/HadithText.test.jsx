// Rendered with renderToStaticMarkup: no jsdom is installed here, and the text a
// reader is shown is all this checks.
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { MARKS } from '../../lib/hadith/hadithWords'
import HadithText from './HadithText'

// Abu Dawud 1's opening, with a narrator named in it and sunnah.com's direction marks.
const arabic = 'حَدَّثَنَا عَبْدُ اللَّهِ، عَنِ الْمُغِيرَةِ، أَنَّ النَّبِيَّ ‏"‏ أَبْعَدَ ‏"‏'
const body = arabic.indexOf('أَنَّ')
const names = [[arabic.indexOf('الْمُغِيرَةِ'), arabic.indexOf('الْمُغِيرَةِ') + 'الْمُغِيرَةِ'.length, 7]]

const arabicShown = (html) => /<p[^>]*dir="rtl"[^>]*>(.*?)<\/p>/s.exec(html)[1].replace(/<[^>]+>/g, '')
const decode = (text) => text.replace(/&quot;/g, '"').replace(/&amp;/g, '&')

describe('HadithText', () => {
  it('prints the hadith as stored, less the invisible direction marks, cut or not', () => {
    for (const cut of [[body - 10, body], null]) {
      const html = renderToStaticMarkup(<HadithText label="1" arabic={arabic} cut={cut} names={names} onNarrator={() => {}} />)
      expect(decode(arabicShown(html))).toBe(arabic.replace(MARKS, ''))
    }
  })

  it('draws the chain quiet and the body in full ink, guessing at nothing without a cut', () => {
    const cut = renderToStaticMarkup(<HadithText label="1" arabic={arabic} cut={[body - 10, body]} />)
    expect(cut).toMatch(/<span class="text-\[var\(--hadith-chain\)\]">حَدَّثَنَا/)
    const none = renderToStaticMarkup(<HadithText label="1" arabic={arabic} />)
    expect(none).not.toContain('text-[var(--hadith-chain)]">حَدَّثَنَا')
  })

  it('with the chain hidden, starts at the teller and keeps the split where it was, marks or no marks', () => {
    // Direction marks before the cut, in what is dropped and in what stays, so both shifts are counted.
    const marked = arabic.replace('عَبْدُ', '\u200fعَبْدُ').replace('الْمُغِيرَةِ', '\u200fالْمُغِيرَةِ')
    const teller = marked.indexOf('عَنِ')
    const cut = [teller, marked.indexOf('أَنَّ')]
    const named = [[marked.indexOf('الْمُغِيرَةِ'), marked.indexOf('الْمُغِيرَةِ') + 'الْمُغِيرَةِ'.length, 7]]
    const html = renderToStaticMarkup(<HadithText label="1" arabic={marked} cut={cut} names={named} hideChain onNarrator={() => {}} />)
    expect(decode(arabicShown(html))).toBe(marked.slice(teller).replace(MARKS, ''))
    const quiet = /<span class="text-\[var\(--hadith-chain\)\]">(.*?)<\/span><span>/s.exec(html)[1].replace(/<[^>]+>/g, '')
    expect(quiet).toBe(marked.slice(teller, cut[1]).replace(MARKS, ''))
  })

  it('sets the English teller line quiet and the rest as written', () => {
    const html = renderToStaticMarkup(<HadithText label="1" arabic={arabic} english={'Narrated Anas: The Prophet said, "Pray."'} />)
    expect(html).toContain('text-[var(--hadith-chain)]">Narrated Anas: </span>The Prophet said, &quot;Pray.&quot;')
  })
})
