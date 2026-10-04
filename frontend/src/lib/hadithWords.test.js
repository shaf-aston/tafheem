import { describe, expect, it } from 'vitest'

import { chainOf, hadithKey, narrated, printedBy, saying } from './hadithWords'

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

describe('chainOf', () => {
  // Real openings from the books, shortened after the first words of the hadith.
  it('ends the chain at the said that no further link follows', () => {
    expect(chainOf('حَدَّثَنَا يَحْيَى بْنُ بُكَيْرٍ، قَالَ حَدَّثَنَا اللَّيْثُ، عَنْ عُقَيْلٍ، عَنْ عَائِشَةَ أُمِّ الْمُؤْمِنِينَ، أَنَّهَا قَالَتْ أَوَّلُ مَا بُدِئَ بِهِ').body)
      .toBe('قَالَتْ أَوَّلُ مَا بُدِئَ بِهِ')
  })

  it('walks through a companion who heard the Prophet to the words', () => {
    const { chain, body } = chainOf('حَدَّثَنَا سُفْيَانُ ، قَالَ : سَمِعْتُ عُمَرَ بْنَ الْخَطَّابِ رَضِيَ اللَّهُ عَنْهُ عَلَى الْمِنْبَرِ، قَالَ سَمِعْتُ رَسُولَ اللَّهِ صلى الله عليه وسلم يَقُولُ ‏"‏ إِنَّمَا الأَعْمَالُ')
    expect(body).toBe('يَقُولُ ‏"‏ إِنَّمَا الأَعْمَالُ')
    expect(chain.startsWith('حَدَّثَنَا')).toBe(true)
  })

  it('keeps a said whose speaker is in the hadith, not the chain', () => {
    expect(chainOf('حَدَّثَنَا آدَمُ، قَالَ سَمِعْتُ أَبَا صَالِحٍ، ذَكْوَانَ يُحَدِّثُ عَنْ أَبِي سَعِيدٍ الْخُدْرِيِّ،‏.‏ قَالَتِ النِّسَاءُ لِلنَّبِيِّ').body)
      .toBe('قَالَتِ النِّسَاءُ لِلنَّبِيِّ')
  })

  it('reads a second chain joined by ح', () => {
    expect(chainOf('حَدَّثَنَا عَبْدَانُ، عَنِ الزُّهْرِيِّ، ح وَحَدَّثَنَا بِشْرٌ، عَنِ الزُّهْرِيِّ، قَالَ أَخْبَرَنِي عُبَيْدُ اللَّهِ، عَنِ ابْنِ عَبَّاسٍ، قَالَ كَانَ رَسُولُ اللَّهِ').body)
      .toBe('قَالَ كَانَ رَسُولُ اللَّهِ')
  })

  it('walks through a woman who passed it on', () => {
    expect(chainOf('حَدَّثَنَا يَحْيَى بْنُ سَعِيدٍ، عَنْ يَحْيَى بْنِ أَبِي كَثِيرٍ، قَالَ حَدَّثَتْنِي كَرِيمَةُ بِنْتُ هَمَّامٍ، أَنَّ امْرَأَةً، أَتَتْ عَائِشَةَ').body)
      .toBe('أَنَّ امْرَأَةً، أَتَتْ عَائِشَةَ')
  })

  it('keeps a recitation to the Prophet in the hadith', () => {
    expect(chainOf('حَدَّثَنَا وَكِيعٌ، عَنِ الأَسْوَدِ بْنِ يَزِيدَ، عَنْ عَبْدِ اللَّهِ، قَالَ قَرَأْتُ عَلَى النَّبِيِّ صلى الله عليه وسلم فَهَلْ مِنْ مُذَّكِرٍ').body)
      .toBe('قَالَ قَرَأْتُ عَلَى النَّبِيِّ صلى الله عليه وسلم فَهَلْ مِنْ مُذَّكِرٍ')
  })

  it('leaves the hadith whole where the end of the chain is not plain', () => {
    const text = 'حَدَّثَنَا أَبُو حَيَّانَ التَّيْمِيُّ، بِهَذَا الإِسْنَادِ مِثْلَهُ غَيْرَ أَنَّ فِي رِوَايَتِهِ ‏"‏ إِذَا وَلَدَتِ الأَمَةُ'
    expect(chainOf(text)).toEqual({ chain: '', body: text })
  })

  it('ends the chain at a plain "that" before the story', () => {
    expect(chainOf('حَدَّثَنَا عَبْدُ اللَّهِ بْنُ يُوسُفَ، قَالَ أَخْبَرَنَا مَالِكٌ، عَنْ هِشَامِ بْنِ عُرْوَةَ، عَنْ أَبِيهِ، عَنْ عَائِشَةَ أُمِّ الْمُؤْمِنِينَ ـ رضى الله عنها ـ أَنَّ الْحَارِثَ بْنَ هِشَامٍ ـ رضى الله عنه ـ سَأَلَ').body)
      .toBe('أَنَّ الْحَارِثَ بْنَ هِشَامٍ ـ رضى الله عنه ـ سَأَلَ')
  })

  it('never hides a short report run on from the last name', () => {
    const text = 'حَدَّثَنَا إِسْحَاقُ بْنُ إِبْرَاهِيمَ، عَنْ إِسْمَاعِيلَ، عَنْ قَيْسٍ، كَانَ عَطَاءُ الْبَدْرِيِّينَ خَمْسَةَ آلاَفٍ خَمْسَةَ آلاَفٍ‏.‏ وَقَالَ عُمَرُ لأُفَضِّلَنَّهُمْ'
    expect(chainOf(text)).toEqual({ chain: '', body: text })
  })

  it('never hides a sentence after a full stop', () => {
    const text = 'حَدَّثَنَا مُسَدَّدٌ، عَنْ أَبِيهِ، عَنِ النَّبِيِّ صلى الله عليه وسلم‏.‏ وَذَكَرَ الَّذِي عَقَرَ النَّاقَةَ قَالَ'
    expect(chainOf(text)).toEqual({ chain: '', body: text })
  })

  it('never hides a verse sitting where a name would be', () => {
    const text = 'حَدَّثَنَا يَحْيَى، عَنْ عَائِشَةَ ـ رضى الله عنها – ‏{‏وَالَّذِي تَوَلَّى كِبْرَهُ‏}‏ قَالَتْ عَبْدُ اللَّهِ'
    expect(chainOf(text)).toEqual({ chain: '', body: text })
  })

  it('leaves a hadith with no chain at all whole', () => {
    expect(chainOf('قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم')).toEqual({ chain: '', body: 'قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم' })
    expect(chainOf('')).toEqual({ chain: '', body: '' })
  })
})
