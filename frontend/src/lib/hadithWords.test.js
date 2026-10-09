import { describe, expect, it } from 'vitest'

import HADITH from '../hadith.json'
import { chainLinks, hadithKey, narrated, printedBy, saying, termOf } from './hadithWords'

describe('saying', () => {
  it('marks a quoted stretch as said and the rest as told', () => {
    expect(saying('The Prophet said, "Pray as you have seen me pray." Then he left.')).toEqual([
      { kind: 'told', text: 'The Prophet said,' },
      { kind: 'said', text: 'Pray as you have seen me pray.' },
      { kind: 'told', text: 'Then he left.' },
    ])
  })

  it('reads the Arabic mark with its direction marks around it', () => {
    expect(saying('قَالَ ‏"‏ إِنَّ أَحَدَكُمْ ‏"‏ .')).toEqual([
      { kind: 'told', text: 'قَالَ' },
      { kind: 'said', text: 'إِنَّ أَحَدَكُمْ' },
      { kind: 'told', text: '.' },
    ])
  })

  it('claims nothing when the book marked nothing', () => {
    expect(saying('The Last Hour would not come until fire emits from the Hijaz')).toEqual([
      { kind: 'plain', text: 'The Last Hour would not come until fire emits from the Hijaz' },
    ])
  })

  it('marks only the innermost quote when a telling holds the words said', () => {
    // tirmidhi 1148 as sunnah.com prints it, its mismatched marks and all.
    const said = saying('“My uncle came. So he said: “Let him in.’” She said: “It is only the woman.’ So he said: ‘Indeed he is your uncle.’”')
      .filter((s) => s.kind === 'said').map((s) => s.text)
    expect(said).toEqual(['Let him in.', 'It is only the woman.', 'Indeed he is your uncle.'])
  })

  it('reads ʿayn, hamza and apostrophes as letters, not quotes', () => {
    expect(saying("Ibn 'Abbas met 'Ata' at Allah's house").map((s) => s.kind)).toEqual(['plain'])
    expect(saying('Ibn ‘Abbas said: “Pray.” Aqra’ left.').filter((s) => s.kind === 'said')).toEqual([{ kind: 'said', text: 'Pray.' }])
  })

  it('keeps several sayings apart', () => {
    expect(saying('He said "one" then "two"').filter((s) => s.kind === 'said')).toEqual([
      { kind: 'said', text: 'one' },
      { kind: 'said', text: 'two' },
    ])
  })

  it('has nothing to say about nothing', () => {
    expect(saying('')).toEqual([])
    expect(saying(null)).toEqual([])
  })
})

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
    const { verbs, endings, words } = HADITH.chain.links
    const all = [...words, ...HADITH.chain.says, ...verbs.flatMap((v) => endings.map((e) => v + e))]
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

  it('has nothing to draw for no chain', () => {
    expect(chainLinks('')).toEqual({ main: [], branches: [] })
  })
})
