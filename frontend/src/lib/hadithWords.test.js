import { describe, expect, it } from 'vitest'

import { CHAIN, chainLinks, hadithKey, narrated, printedBy, saying, spoken, termOf } from './hadithWords'

// The said words alone, without the marks around them.
const said = (text) => saying(text).filter((s) => s.kind === 'said').map((s) => s.text)
// The spans put back together: always the book's text, less the direction marks.
const whole = (text) => saying(text).map((s) => s.open + s.text + s.close).join('')

describe('saying', () => {
  it('marks a quoted stretch as said and the rest as told, keeping the marks', () => {
    expect(saying('The Prophet said, "Pray as you have seen me pray." Then he left.')).toEqual([
      { kind: 'told', open: '', text: 'The Prophet said, ', close: '' },
      { kind: 'said', open: '"', text: 'Pray as you have seen me pray.', close: '"' },
      { kind: 'told', open: '', text: ' Then he left.', close: '' },
    ])
  })

  it('closes an Arabic mark that has a space before it and a full stop after (Bukhari 59)', () => {
    const text = 'قَالَ ‏"‏ أَيْنَ السَّائِلُ ‏"‏‏.‏ قَالَ هَا أَنَا ‏.‏ قَالَ ‏"‏ فَإِذَا ضُيِّعَتِ الأَمَانَةُ ‏"‏‏.‏'
    expect(said(text)).toEqual([' أَيْنَ السَّائِلُ ', ' فَإِذَا ضُيِّعَتِ الأَمَانَةُ '])
  })

  it('reads the Arabic mark with its direction marks around it', () => {
    expect(said('قَالَ ‏"‏ إِنَّ أَحَدَكُمْ ‏"‏ .')).toEqual([' إِنَّ أَحَدَكُمْ '])
    expect(said('قَالَ «بِهَذَا أُمِرْتُ» . فَقَالَ')).toEqual(['بِهَذَا أُمِرْتُ'])
  })

  it('closes an Arabic quote whose mark has a space before it and a full stop after', () => {
    // Bukhari 59: the Prophet's words are quoted, the Bedouin's are not.
    const text = 'قَالَ \u200f"\u200f أَيْنَ السَّائِلُ \u200f"\u200f\u200f.\u200f قَالَ هَا أَنَا\u200f.\u200f قَالَ \u200f"\u200f فَانْتَظِرِ السَّاعَةَ \u200f"\u200f\u200f.\u200f'
    const kinds = saying(text).map((s) => [s.kind, s.text.trim()])
    expect(kinds).toEqual([
      ['told', 'قَالَ'], ['said', 'أَيْنَ السَّائِلُ'], ['told', '. قَالَ هَا أَنَا. قَالَ'], ['said', 'فَانْتَظِرِ السَّاعَةَ'], ['told', '.'],
    ])
  })

  it('closes an Arabic quote whose mark has a space before it and an Arabic comma after', () => {
    // Bukhari 4372: "release Thumama", then the telling goes on.
    const text = 'فَقَالَ " أَطْلِقُوا ثُمَامَةَ "، فَانْطَلَقَ إِلَى نَخْلٍ'
    const kinds = saying(text).map((s) => [s.kind, s.text.trim()])
    expect(kinds).toEqual([['told', 'فَقَالَ'], ['said', 'أَطْلِقُوا ثُمَامَةَ'], ['told', '، فَانْطَلَقَ إِلَى نَخْلٍ']])
  })

  it('reads a single mark after an abbreviated "b." as the ʿayn of a name', () => {
    // Abu Dawud 169: ‘Uqbah b. ‘Amir ... b.’Amir is a name, not a quote from the first ‘ to here.
    const text = '‘Uqbah b. ‘Amir said: We served ourselves. Narrated on the authority of ‘Uqbah b.’Amir'
    expect(saying(text).map((s) => s.kind)).toEqual(['plain'])
  })

  it('claims nothing when the book marked nothing', () => {
    expect(saying('The Last Hour would not come until fire emits from the Hijaz')).toEqual([
      { kind: 'plain', open: '', text: 'The Last Hour would not come until fire emits from the Hijaz', close: '' },
    ])
  })

  it('never changes a letter: the spans joined are the text', () => {
    for (const text of [
      'Once in \'Iraq, Al-Mughira said, \'O Mughira! said, \'I was ordered?\'" Then',
      "Ibn 'Abbas met 'Ata' at Allah's house and Hira' too",
      '“Let him in.’” She said: “It is', 'He said "one', 'a " stray', '\'', '"',
    ]) expect(whole(text)).toBe(text)
  })

  it('takes the ʿayn of a name for a letter even inside a quote (bukhari 522)', () => {
    const text = 'went to him and said, "Once in \'Iraq, Al-Mughira delayed and Abi Mas`ud said, \'O Mughira! Gabriel came and said, \'I was ordered to do so?\'" `Umar said to `Urwa, "Be sure of what you Say."'
    const spans = saying(text)
    expect(spans[1]).toMatchObject({ kind: 'told', open: '"' })
    expect(spans[1].text.startsWith('Once in \'Iraq')).toBe(true)
    expect(said(text)).toEqual(['I was ordered to do so?', 'Be sure of what you Say.'])
  })

  it('marks only the innermost quote when a telling holds the words said', () => {
    // tirmidhi 1148 as sunnah.com prints it, its mismatched marks and all.
    expect(said('“My uncle came. So he said: “Let him in.’” She said: “It is only the woman.’ So he said: ‘Indeed he is your uncle.’”'))
      .toEqual(['Let him in.', 'It is only the woman.', 'Indeed he is your uncle.'])
  })

  it('closes a quote opened with \' and closed with ", as the books sometimes mix them', () => {
    // bukhari 947 as sunnah.com prints it.
    expect(said('He rode and said, \'Allahu Akbar! Khaibar is ruined." The people came out into the streets saying, "Muhammad and his army." Allah\'s Messenger vanquished them'))
      .toEqual(['Allahu Akbar! Khaibar is ruined.', 'Muhammad and his army.'])
  })

  it('reads a straight " by its place: a quote inside a quote opens, a mark after the words closes', () => {
    // bukhari 3268, its mismatched marks and all.
    expect(said('He said, "Two persons came to me. One of them asked the other, "What is the ailment of this man?" The other replied, \'He has been bewitched" The first asked, \'Who has bewitched him?\' " So, the Prophet went out'))
      .toEqual(['What is the ailment of this man?', 'He has been bewitched', 'Who has bewitched him?'])
  })

  it('opens a " after a colon whichever side its space is on (muslim 7134)', () => {
    expect(said('He then recited:" No soul knows what comfort has been hidden')).toEqual([' No soul knows what comfort has been hidden'])
  })

  it('does not take a name\'s ʿayn for a quote that " then closes', () => {
    expect(said('He said, "Go to \'Ali." Then he left.')).toEqual(["Go to 'Ali."])
    // bukhari 6253 and nasai 4615.
    expect(said('She replied, "Wa \'alaihi-s- Salam." (Peace be on him)')).toEqual(["Wa 'alaihi-s- Salam."])
    expect(said('He said: \'We paid in the time of Abu Bakr and \'Umar, for wheat." And I asked')).toEqual(["We paid in the time of Abu Bakr and 'Umar, for wheat."])
    // tirmidhi 3804: the second ' is ʿAbd's, inside a quote that opened after the colon.
    expect(said("it was said to him: 'O Abu 'Abdur-Rahman, advise us.' He said: 'Sit me up.'")).toEqual(["O Abu 'Abdur-Rahman, advise us.", 'Sit me up.'])
  })

  it('reads ʿayn, hamza and apostrophes as letters, not quotes', () => {
    expect(saying("Ibn 'Abbas met 'Ata' at Allah's house").map((s) => s.kind)).toEqual(['plain'])
    expect(said('Ibn ‘Abbas said: “Pray.” Aqra’ left.')).toEqual(['Pray.'])
    // tirmidhi 1254: two names' marks, not a quote between them.
    expect(said('[Abu \'Eisa said:] This Hadith is Hasan Sahih. We do not know of it being Marfu\' except by the narration of \'Amir')).toEqual([])
  })

  it('takes a \' quote that opens mid-sentence when it ends like one (bukhari 4, nasai 4006)', () => {
    expect(said('up to \'and desert the idols.\' (74.1-5)')).toEqual(['and desert the idols.'])
    expect(said('This Verse - \'And whoever kills a believer intentionally, his recompense is Hell\' - was revealed')).toEqual(['And whoever kills a believer intentionally, his recompense is Hell'])
  })

  it('reads a " after a comma as the close it is (bukhari 7336)', () => {
    expect(said('`Abdullah said, "The Prophet arranged for a horse race," `Abdullah was one of those')).toEqual(['The Prophet arranged for a horse race,'])
  })

  it('opens a \' quote before an ellipsis or a bracket (bukhari 7313)', () => {
    expect(said("revealed: '..or from beneath your feet.' (6.65)")).toEqual(['..or from beneath your feet.'])
    expect(said("He said: '(He prayed) two rak'ahs.' Then")).toEqual(["(He prayed) two rak'ahs."])
  })

  it('lets a saying the book never closed run to the end', () => {
    expect(said('`Urwa added, "Aisha told me that he used to pray')).toEqual(['Aisha told me that he used to pray'])
  })

  it('keeps several sayings apart', () => {
    expect(said('He said "one" then "two"')).toEqual(['one', 'two'])
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

describe('spoken', () => {
  const joined = (spans) => spans.map((s) => s.open + s.text + s.close).join('')
  const said = (spans) => spans.filter((s) => s.kind === 'said').map((s) => s.text).join('')

  it('starts an unmarked saying after the verb and the Prophet who says it', () => {
    const text = 'عَنْ أَنَسٍ، قَالَ قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم لاَ يُؤْمِنُ أَحَدُكُمْ'
    const spans = spoken(text, text.indexOf('قَالَ رَسُولُ'))
    expect(said(spans)).toBe('لاَ يُؤْمِنُ أَحَدُكُمْ')
    expect(joined(spans)).toBe(text)
  })

  it('steps past a named speaker and to whom, but keeps a saying that opens with قلتُ', () => {
    const named = 'فَقَالَ عُمَرُ لَهُ قَدْ عَرَفْنَا ذَلِكَ'
    expect(said(spoken(named))).toBe('قَدْ عَرَفْنَا ذَلِكَ')
    const own = 'فَقَالَ حَلَقْتُ قَبْلَ أَنْ أَذْبَحَ'
    expect(said(spoken(own))).toBe('حَلَقْتُ قَبْلَ أَنْ أَذْبَحَ')
  })

  it('takes the last verb that leaves words to say, past a trailing aside', () => {
    expect(said(spoken('ثُمَّ قَالَ صَلُّوا كَمَا رَأَيْتُمُونِي قَالَ أَنَسٌ.'))).toBe('صَلُّوا كَمَا رَأَيْتُمُونِي قَالَ أَنَسٌ.')
  })

  it('reads no verb in the chain, and leaves a hadith with no verb or with marks as saying() does', () => {
    const chain = 'حَدَّثَنَا مَالِكٌ قَالَ حَدَّثَنَا نَافِعٌ'
    expect(spoken(chain, chain.length)).toEqual(saying(chain))
    expect(spoken('كَانَ النَّبِيُّ يُصَلِّي')).toEqual(saying('كَانَ النَّبِيُّ يُصَلِّي'))
    const marked = 'قَالَ "صَلُّوا"'
    expect(spoken(marked)).toEqual(saying(marked))
  })
})
