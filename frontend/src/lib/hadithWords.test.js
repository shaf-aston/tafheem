import { describe, expect, it } from 'vitest'

import { CHAIN, chainAndBody, chainLinks, hadithKey, MARKS, narrated, printedBy, termOf } from './hadithWords'

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

describe('termOf', () => {
  it('has a guide entry for every word the chain walker reads', () => {
    const { verbs, endings, words } = CHAIN.links
    const all = [...words, ...CHAIN.says, ...verbs.flatMap((v) => endings.map((e) => v + e))]
    expect(all.filter((word) => !termOf(word))).toEqual([])
  })

  it('finds a verb by its stem, joined wa and vowels and all', () => {
    expect(termOf('وَحَدَّثَتْنِي').way).toBe('heard')
    expect(termOf('عَنْ').way).toBe('loose')
  })
})

describe('chainLinks', () => {
  // The chain is what comes before `body`, as the server cuts it.
  const links = (text, body) => chainLinks(text.slice(0, text.lastIndexOf(body)).trim())

  it('gives the verb after a name handed on by أن to that name, as the weak points read it', () => {
    const { main } = links('حَدَّثَنَا أَبَانُ، حَدَّثَنَا قَتَادَةُ، أَنَّ مُحَمَّدَ بْنَ سِيرِينَ، حَدَّثَهُ عَنْ أَبِي هُرَيْرَةَ، قَالَ كَانَ', 'قَالَ كَانَ')
    expect(main.map(({ term, name }) => [term, name])).toEqual([
      ['حَدَّثَنَا', 'أَبَانُ'], ['حَدَّثَنَا', 'قَتَادَةُ'], ['حَدَّثَهُ', 'مُحَمَّدَ بْنَ سِيرِينَ'], ['عَنْ', 'أَبِي هُرَيْرَةَ'],
    ])
  })

  it('names each narrator with the word that passed it on', () => {
    const { main, branches } = links('حَدَّثَنَا الْحُمَيْدِيُّ، قَالَ حَدَّثَنَا سُفْيَانُ، عَنْ يَحْيَى بْنِ سَعِيدٍ، قَالَ سَمِعْتُ عُمَرَ، قَالَ سَمِعْتُ رَسُولَ اللَّهِ صلى الله عليه وسلم يَقُولُ ‏"‏ إِنَّمَا', 'يَقُولُ')
    expect(main.map(({ term, way, name }) => [term, way, name])).toEqual([
      ['حَدَّثَنَا', 'heard', 'الْحُمَيْدِيُّ'],
      ['حَدَّثَنَا', 'heard', 'سُفْيَانُ'],
      ['عَنْ', 'loose', 'يَحْيَى بْنِ سَعِيدٍ'],
      ['سَمِعْتُ', 'heard', 'عُمَرَ'],
      ['سَمِعْتُ', 'heard', 'رَسُولَ اللَّهِ صلى الله عليه وسلم'],
    ])
    expect(branches).toEqual([])
  })

  it('joins a second chain at the first narrator both name, in any case ending', () => {
    const { main, branches } = links('حَدَّثَنَا مُحَمَّدُ بْنُ يُوسُفَ، قَالَ حَدَّثَنَا سُفْيَانُ، عَنْ عَمْرِو بْنِ عَامِرٍ، قَالَ سَمِعْتُ أَنَسًا، ح قَالَ وَحَدَّثَنَا مُسَدَّدٌ، قَالَ حَدَّثَنَا يَحْيَى، عَنْ سُفْيَانَ، قَالَ حَدَّثَنِي عَمْرُو بْنُ عَامِرٍ، عَنْ أَنَسٍ، قَالَ كَانَ', 'قَالَ كَانَ')
    expect(main.map((l) => l.name)).toEqual(['مُسَدَّدٌ', 'يَحْيَى', 'سُفْيَانَ', 'عَمْرُو بْنُ عَامِرٍ', 'أَنَسٍ'])
    expect(branches).toEqual([{
      links: [expect.objectContaining({ name: 'مُحَمَّدُ بْنُ يُوسُفَ' })],
      at: 2,
      join: expect.objectContaining({ term: 'حَدَّثَنَا', name: 'سُفْيَانُ' }),
    }])
  })

  it('joins where the books say both passed it on', () => {
    const { main, branches } = links('وَحَدَّثَنَا أَبُو بَكْرِ بْنُ أَبِي شَيْبَةَ، حَدَّثَنَا أَبُو خَالِدٍ الأَحْمَرُ، ح وَحَدَّثَنِيهِ زُهَيْرُ بْنُ حَرْبٍ، حَدَّثَنَا يَزِيدُ بْنُ هَارُونَ، كِلاَهُمَا عَنْ أَبِي مَالِكٍ، عَنْ أَبِيهِ، أَنَّهُ سَمِعَ النَّبِيَّ صلى الله عليه وسلم يَقُولُ مَنْ', 'يَقُولُ مَنْ')
    expect(main[branches[0].at].name).toBe('أَبِي مَالِكٍ')
    expect(branches[0].links.map((l) => l.name)).toEqual(['أَبُو بَكْرِ بْنُ أَبِي شَيْبَةَ', 'أَبُو خَالِدٍ الأَحْمَرُ'])
  })

  it('does not join two strands on "my father", nor claim a meeting the books do not name', () => {
    const { branches } = links('حَدَّثَنَا مُحَمَّدُ بْنُ سِنَانٍ، قَالَ حَدَّثَنَا فُلَيْحٌ، ح وَحَدَّثَنِي إِبْرَاهِيمُ بْنُ الْمُنْذِرِ، قَالَ حَدَّثَنَا مُحَمَّدُ بْنُ فُلَيْحٍ، قَالَ حَدَّثَنِي أَبِي قَالَ، حَدَّثَنِي هِلاَلُ بْنُ عَلِيٍّ، عَنْ عَطَاءِ بْنِ يَسَارٍ، عَنْ أَبِي هُرَيْرَةَ، أَنَّ رَسُولَ اللَّهِ', 'أَنَّ رَسُولَ اللَّهِ')
    expect(branches[0].at).toBeNull()
  })

  it('keeps الله in a name, so عبد الله never joins عبد الرحمن', () => {
    const { branches } = links('حَدَّثَنَا قُتَيْبَةُ، حَدَّثَنَا عَبْدُ اللَّهِ، ح وَحَدَّثَنَا مُسَدَّدٌ، حَدَّثَنَا عَبْدُ الرَّحْمَنِ بْنُ مَهْدِيٍّ، عَنْ سُفْيَانَ، قَالَ كَانَ', 'قَالَ كَانَ')
    expect(branches[0].at).toBeNull()
  })

  it('leaves a remark set between aside marks out of the name, and ignores a mark with no partner', () => {
    const { main } = links('حَدَّثَنَا عَبْدُ اللَّهِ، حَدَّثَنَا عَبْدُ الْعَزِيزِ، - يَعْنِي ابْنَ مُحَمَّدٍ - عَنْ مُحَمَّدٍ، - يَعْنِي ابْنَ عَمْرٍو - عَنْ أَبِي سَلَمَةَ، - عَنِ الْمُغِيرَةِ، أَنَّ النَّبِيَّ', 'أَنَّ النَّبِيَّ')
    expect(main.map(({ name }) => name)).toEqual(['عَبْدُ اللَّهِ', 'عَبْدُ الْعَزِيزِ', 'مُحَمَّدٍ', 'أَبِي سَلَمَةَ', 'الْمُغِيرَةِ'])
  })

  it('has nothing to draw for no chain', () => {
    expect(chainLinks('')).toEqual({ main: [], branches: [] })
  })
})

describe('chainAndBody', () => {
  // Abu Dawud 1 and 5 as sunnah.com gives them, direction marks and all: 1 with the
  // server's cut ([teller_at, body_at]), 5 with none (a second chain for a hadith before it).
  const withCut = { arabic: "\u062d\u064e\u062f\u0651\u064e\u062b\u064e\u0646\u064e\u0627 \u0639\u064e\u0628\u0652\u062f\u064f \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0628\u0652\u0646\u064f \u0645\u064e\u0633\u0652\u0644\u064e\u0645\u064e\u0629\u064e \u0628\u0652\u0646\u0650 \u0642\u064e\u0639\u0652\u0646\u064e\u0628\u064d \u0627\u0644\u0652\u0642\u064e\u0639\u0652\u0646\u064e\u0628\u0650\u064a\u0651\u064f\u060c \u062d\u064e\u062f\u0651\u064e\u062b\u064e\u0646\u064e\u0627 \u0639\u064e\u0628\u0652\u062f\u064f \u0627\u0644\u0652\u0639\u064e\u0632\u0650\u064a\u0632\u0650\u060c - \u064a\u064e\u0639\u0652\u0646\u0650\u064a \u0627\u0628\u0652\u0646\u064e \u0645\u064f\u062d\u064e\u0645\u0651\u064e\u062f\u064d - \u0639\u064e\u0646\u0652 \u0645\u064f\u062d\u064e\u0645\u0651\u064e\u062f\u064d\u060c - \u064a\u064e\u0639\u0652\u0646\u0650\u064a \u0627\u0628\u0652\u0646\u064e \u0639\u064e\u0645\u0652\u0631\u064d\u0648 - \u0639\u064e\u0646\u0652 \u0623\u064e\u0628\u0650\u064a \u0633\u064e\u0644\u064e\u0645\u064e\u0629\u064e\u060c \u0639\u064e\u0646\u0650 \u0627\u0644\u0652\u0645\u064f\u063a\u0650\u064a\u0631\u064e\u0629\u0650 \u0628\u0652\u0646\u0650 \u0634\u064f\u0639\u0652\u0628\u064e\u0629\u064e\u060c \u0623\u064e\u0646\u0651\u064e \u0627\u0644\u0646\u0651\u064e\u0628\u0650\u064a\u0651\u064e \u0635\u0644\u0649 \u0627\u0644\u0644\u0647 \u0639\u0644\u064a\u0647 \u0648\u0633\u0644\u0645 \u0643\u064e\u0627\u0646\u064e \u0625\u0650\u0630\u064e\u0627 \u0630\u064e\u0647\u064e\u0628\u064e \u0627\u0644\u0652\u0645\u064e\u0630\u0652\u0647\u064e\u0628\u064e \u0623\u064e\u0628\u0652\u0639\u064e\u062f\u064e \u200f.\u200f", cut: [193, 226] }
  const noCut = { arabic: "\u062d\u064e\u062f\u064e\u0651\u062b\u064e\u0646\u064e\u0627 \u0627\u0644\u0652\u062d\u064e\u0633\u064e\u0646\u064f \u0628\u0652\u0646\u064f \u0639\u064e\u0645\u0652\u0631\u064d\u0648\u060c - \u064a\u064e\u0639\u0652\u0646\u0650\u064a \u0627\u0644\u0633\u064e\u0651\u062f\u064f\u0648\u0633\u0650\u064a\u064e\u0651 - \u062d\u064e\u062f\u064e\u0651\u062b\u064e\u0646\u064e\u0627 \u0648\u064e\u0643\u0650\u064a\u0639\u064c\u060c \u0639\u064e\u0646\u0652 \u0634\u064f\u0639\u0652\u0628\u064e\u0629\u064e\u060c \u0639\u064e\u0646\u0652 \u0639\u064e\u0628\u0652\u062f\u0650 \u0627\u0644\u0652\u0639\u064e\u0632\u0650\u064a\u0632\u0650\u060c - \u0647\u064f\u0648\u064e \u0627\u0628\u0652\u0646\u064f \u0635\u064f\u0647\u064e\u064a\u0652\u0628\u064d - \u0639\u064e\u0646\u0652 \u0623\u064e\u0646\u064e\u0633\u064d\u060c \u0628\u0650\u0647\u064e\u0630\u064e\u0627 \u0627\u0644\u0652\u062d\u064e\u062f\u0650\u064a\u062b\u0650 \u0642\u064e\u0627\u0644\u064e \u200f\"\u200f \u0627\u0644\u0644\u064e\u0651\u0647\u064f\u0645\u064e\u0651 \u0625\u0650\u0646\u0650\u0651\u064a \u0623\u064e\u0639\u064f\u0648\u0630\u064f \u0628\u0650\u0643\u064e \u200f\"\u200f \u200f.\u200f \u0648\u064e\u0642\u064e\u0627\u0644\u064e \u0634\u064f\u0639\u0652\u0628\u064e\u0629\u064f \u0648\u064e\u0642\u064e\u0627\u0644\u064e \u0645\u064e\u0631\u064e\u0651\u0629\u064b \u200f\"\u200f \u0623\u064e\u0639\u064f\u0648\u0630\u064f \u0628\u0650\u0627\u0644\u0644\u064e\u0651\u0647\u0650 \u200f\"\u200f \u200f.\u200f", cut: null }
  const joined = (parts) => parts.map((part) => part.text).join('')

  it('gives back every letter and mark of the hadith but the invisible direction marks', () => {
    for (const { arabic, cut } of [withCut, noCut]) {
      expect(joined(chainAndBody(arabic, cut?.[1] ?? null))).toBe(arabic.replace(MARKS, ''))
    }
  })

  it('draws the chain up to where the server says the body starts, the teller with it', () => {
    const [chain, body] = chainAndBody(withCut.arabic, withCut.cut[1])
    expect(chain.kind).toBe('chain')
    expect(chain.text).toBe(withCut.arabic.slice(0, withCut.cut[1]))
    expect(body.kind).toBe('body')
    expect(body.text).toBe(withCut.arabic.slice(withCut.cut[1]).replace(MARKS, ''))
  })

  it('guesses nothing where no cut is known: all of it is the body', () => {
    expect(chainAndBody(noCut.arabic).map((part) => part.kind)).toEqual(['body'])
  })

  it('counts the direction marks before the body', () => {
    const text = '\u200fحَدَّثَنَا مَالِكٌ، كَانَ يُصَلِّي'
    expect(chainAndBody(text, text.indexOf('كَانَ'))).toEqual([
      { kind: 'chain', text: 'حَدَّثَنَا مَالِكٌ، ' },
      { kind: 'body', text: 'كَانَ يُصَلِّي' },
    ])
  })

  it('has nothing for no text, and no empty chain for a cut at 0', () => {
    expect(chainAndBody('')).toEqual([])
    expect(chainAndBody(null)).toEqual([])
    expect(chainAndBody('كَانَ', 0)).toEqual([{ kind: 'body', text: 'كَانَ' }])
  })
})
