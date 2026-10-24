import { describe, expect, it } from 'vitest'

import { laneEntry, mendWords, plainEntry, tidyNotes } from './laneEntry'

const FSI = '⁨'
const PDI = '⁩'
const ar = (word) => `${FSI}${word}${PDI}`

describe('mendWords', () => {
  it('joins a word the dump split with ^', () => {
    expect(mendWords(`${ar('ا')}^${ar('َنَارَ')}`)).toBe(ar('اَنَارَ'))
  })

  it('joins one split with @ too', () => {
    expect(mendWords(`${ar('وَا')}@${ar('لْأَرْضِ')}`)).toBe(ar('وَالْأَرْضِ'))
  })

  it('leaves a caret that is not between two Arabic runs alone', () => {
    expect(mendWords('2^3')).toBe('2^3')
  })

  it('joins one split at a lost hamza with =', () => {
    expect(mendWords(`${ar('شَا')}=${ar('ءَهُ')}`)).toBe(ar('شَاءَهُ'))
  })

  it('writes the madda an = after an alif stands for', () => {
    expect(mendWords(`${ar('مَا')}=${ar('بٌ')}`)).toBe(ar('مَآبٌ'))
  })

  it('leaves an = that is not between two Arabic runs alone', () => {
    expect(mendWords('the sign =')).toBe('the sign =')
  })

  it('takes the bar out of a hamzated alif', () => {
    expect(mendWords(ar('اـِذَا'))).toBe(ar('اِذَا'))
  })

  it('leaves a tatweel that is not carrying a hamza', () => {
    expect(mendWords(ar('كـتاب'))).toBe(ar('كـتاب'))
  })
})

describe('plainEntry', () => {
  it('turns a sub-sense mark into the break it stands for', () => {
    expect(plainEntry(`He struck it. (M.) ― -b2- And ${ar('صَدَمَهُ')}`))
      .toBe(`He struck it. (M.)
And ${ar('صَدَمَهُ')}`)
  })

  it('leaves a book that carries none of the marks exactly as it is', () => {
    expect(plainEntry(ar('الحمد لله'))).toBe(ar('الحمد لله'))
  })

  it('gives back nothing for nothing', () => {
    expect(plainEntry(undefined)).toBe('')
  })
})

describe('laneEntry', () => {
  it('gives back nothing for nothing', () => {
    expect(laneEntry('')).toEqual([])
    expect(laneEntry(undefined)).toEqual([])
  })

  it('reads a book with no markup as one plain block', () => {
    const [only] = laneEntry('A plain sentence.')
    expect(only.form).toBe(null)
    expect(only.senses).toHaveLength(1)
    expect(only.senses[0].pieces[0]).toEqual({ kind: 'text', text: 'A plain sentence.' })
  })

  it('cuts the entry at each verb form heading', () => {
    const raw = `1 ${ar('نَارَ')} shone. (S.) 2 ${ar('نوّر')} lit. (K.) 10 ${ar('استنور')} sought light. (TA.)`
    expect(laneEntry(raw).map((f) => f.form)).toEqual(['1', '2', '10'])
  })

  it('does not read a digit inside a sentence as a heading', () => {
    // Lane refers to other forms constantly; "see 4" must stay prose.
    const raw = `1 ${ar('نَارَ')} see 4, in two places, and 10 ${ar('استنور')} as well.`
    expect(laneEntry(raw)).toHaveLength(1)
  })

  it('keeps whatever stands before the first heading', () => {
    const raw = `${ar('نور')} the root. 1 ${ar('نَارَ')} shone.`
    const forms = laneEntry(raw)
    expect(forms[0].form).toBe(null)
    expect(forms[1].form).toBe('1')
  })

  it('numbers the senses and the sub-senses under a form', () => {
    const raw = `1 ${ar('نَارَ')} first. -A2- second. ― -b2- a finer point. -A3- third.`
    const [form] = laneEntry(raw)
    expect(form.senses.map((s) => [s.kind, s.number])).toEqual([
      ['sense', 1],
      ['sense', 2],
      ['sub', 2],
      ['sense', 3],
    ])
  })

  it('marks the authorities apart from the prose', () => {
    const [form] = laneEntry('It shone. (S, A, Msb, K.)')
    expect(form.senses[0].pieces).toEqual([
      { kind: 'text', text: 'It shone. ' },
      { kind: 'cite', text: '(S, A, Msb, K.)' },
    ])
  })

  it('marks a bracketed aside as a citation too', () => {
    const [form] = laneEntry('It shone [says Lane].')
    expect(form.senses[0].pieces.map((p) => p.kind)).toEqual(['text', 'cite', 'text'])
  })

  it('marks the tropical tag as a tag, not an authority', () => {
    const [form] = laneEntry('(tropical:) It shone. (S.)')
    expect(form.senses[0].pieces.map((p) => p.kind)).toEqual(['tag', 'text', 'cite'])
  })

  it('lifts the opening word of each section into its heading', () => {
    const forms = laneEntry(`1 ${ar('آبَ')}, aor. x. (S.)\n${ar('أَوْبٌ')} and ${ar('إِيَابٌ')} Return.`)
    expect(forms.map((f) => f.word)).toEqual(['آبَ', 'أَوْبٌ'])
    expect(forms[0].senses[0].pieces[0].text).toBe('aor. x. ')
    expect(forms[1].senses[0].pieces[0].text).toBe(`and ${ar('إِيَابٌ')} Return.`)
  })

  it('drops the unvowelled copy after a heading word, not a second word', () => {
    const words = laneEntry(`${ar('مَآبٌ مآب')} A place.\n${ar('رِيحٌ مُؤْوِبَةٌ')} A wind.`).map((f) => f.word)
    expect(words).toEqual(['مَآبٌ', 'رِيحٌ مُؤْوِبَةٌ'])
  })

  it('leaves a section that opens in English without a word', () => {
    expect(laneEntry('Q. Q. see 1.')[0].word).toBe(null)
  })

  it('starts a new headword at each line, since the book broke it there', () => {
    const raw = `1 ${ar('عَلِمَهُ')} He knew it.\n${ar('عِلْمٌ')} is an inf. n.`
    const forms = laneEntry(raw)
    expect(forms.map((f) => f.form)).toEqual(['1', null])
  })
})

describe('the verses', () => {
  const kind = (raw) => laneEntry(raw)[0].senses[0].pieces
  const refs = (raw) => kind(raw).filter((p) => p.kind === 'ref').map((p) => p.text)

  it('reads a bracketed sura and verse', () => {
    expect(refs('it is said in the Kur [viii. 62], meaning')).toEqual(["Qur'án 8:62"])
  })

  it('reads one written without brackets', () => {
    expect(refs('in the Kur xii. 68 it means')).toEqual(["Qur'án 12:68"])
  })

  it('keeps both when one bracket holds two', () => {
    expect(refs('in the Kur [lvi. 9 and xc. 19],')).toEqual(["Qur'án 56:9 and 90:19"])
  })

  it('leaves a numeral that is not a verse alone', () => {
    // The nearest thing that looks the same: Lane numbers Freytag's proverbs
    // and Baydawi's commentary this way, 1,332 times, and none are suras.
    const raw = "see Freytag's Arab. Prov. ii. 119, and (Bd in iv. 68.)"
    expect(refs(raw)).toEqual([])
    expect(kind(raw).map((p) => p.text).join('')).toBe(raw)
  })

  it('leaves a sura out of range alone', () => {
    // cxx is 120; the book has 114.
    expect(refs('in the Kur cxx. 3')).toEqual([])
  })

  it('reads one quoted inside an aside of his own', () => {
    const [piece] = kind('[in the Kur ii. 5, meaning thus].')
    expect(piece).toEqual({ kind: 'cite', text: "[in the Qur'án 2:5, meaning thus]" })
  })
})

describe('tidy view', () => {
  // Cut from the entry on شرك the operator asked to be made readable.
  const raw = `${ar('شِرْكَةٌ')} (S, Mgh, * Msb, K) and ${ar('شَرِكَةٌ')}, the former a contraction`
    + ` of the latter, (Msb,) or ${ar('شِرْكٌ')} [q. v. infrà] is a simple subst., (S, K,)`
    + ` [He shared, participated, or partook, with him in it;] and ${ar('فيه')} ↓ ${ar('شاركهُ')}`
    + ` [signifies the same]. (Mgh, Msb, * K.)`

  it('drops the authorities and pointers, keeps the meaning', () => {
    const said = tidyNotes(raw)
    for (const mark of ['(S,', 'Msb', '(Mgh', 'q. v.', 'infrà', '↓', '*', '[]']) {
      expect(said).not.toContain(mark)
    }
    expect(said).toContain('[He shared, participated, or partook, with him in it;]')
    expect(said).toContain('[signifies the same].')
    expect(said).toContain(`${ar('شِرْكٌ')} is a simple subst.,`)
  })

  it('keeps a note Lane opened inside an authority list', () => {
    expect(tidyNotes('the same. (Mgh, Msb, * K. * [It is said in the TA, rarely.]) And')).toBe(
      'the same. [It is said in the TA, rarely.] And')
  })

  it('does the same when the dump lost the closing parenthesis', () => {
    expect(tidyNotes('the same. (Mgh, Msb, * K. * [It is said in the TA.] And')).toBe(
      'the same. [It is said in the TA.] And')
  })

  it('leaves a bracket after prose in parentheses alone', () => {
    expect(tidyNotes('(as some say [rarely])')).toBe('(as some say [rarely])')
  })

  it('keeps the word sharing a parenthesis with authorities', () => {
    expect(tidyNotes(`a road (${ar('طَرِيق')}, Mgh, Msb, TA), is`)).toBe(`a road (${ar('طَرِيق')}), is`)
  })

  it('keeps the name that says who a pronoun means', () => {
    expect(tidyNotes('(S, K,) He (God) created him. (TA.)').trim()).toBe('He (God) created him.')
    const text = laneEntry('It shone. (S.) He (God) made it. (K.)', { tidy: true })[0].senses[0].pieces
    expect(text.map((p) => p.text).join('').trim()).toBe('It shone. He (God) made it.')
  })

  it('still drops an authority after a pronoun that names nobody', () => {
    // The nearest case: "it (K)" ends a clause, and the K is the source.
    expect(tidyNotes('he gave it (K) to them')).toBe('he gave it to them')
  })

  it('drops "&c." with the list it closes', () => {
    expect(tidyNotes('he returned, (T, S, &c.,) and').trim()).toBe('he returned, and')
    expect(tidyNotes('(&c.)')).toBe('')
  })

  it('drops a lone abbreviation beside prose, but not the pronoun I', () => {
    expect(tidyNotes('He (an absent person, T) returned')).toBe('He (an absent person) returned')
    expect(tidyNotes('(as said, I)')).toBe('(as said, I)')
  })

  it('breaks a long sense where Lane closes a statement with its sources', () => {
    const [form] = laneEntry('1 x at night: (M, TA:) or he came. (S.)'.replace('x', ar('آبَ')), { tidy: true })
    expect(form.senses.map((s) => s.number)).toEqual([1, 0])
    expect(form.senses[1].pieces.map((p) => p.text).join('').trim()).toBe('or he came.')
    expect(plainEntry('at night: (M, TA:) or he came.', { tidy: true })).toBe('at night:\nor he came.')
  })

  it('does not break at a colon that ends prose in brackets', () => {
    const [form] = laneEntry('he said (as some say:) or not.', { tidy: true })
    expect(form.senses).toHaveLength(1)
  })

  it('drops a bare "and the rest" bracket and the doubled colon it leaves', () => {
    expect(tidyNotes('Returning: [&c.:]: pl.')).toBe('Returning: pl.')
    const text = laneEntry('Returning: [&c.:]: pl.', { tidy: true })[0].senses[0].pieces
    expect(text.map((p) => p.text).join('')).toBe('Returning: pl.')
  })

  it('keeps a lone capitalised word in prose', () => {
    expect(tidyNotes('(meaning, Persian)')).toBe('(meaning, Persian)')
  })

  it('leaves prose and the figurative tag in parentheses alone', () => {
    expect(tidyNotes('he said (tropical:) and (as some say)')).toBe('he said (tropical:) and (as some say)')
  })

  it('does not take a note with lowercase words for an authority', () => {
    // The nearest thing to an authority list that is not one.
    expect(tidyNotes('(Bd in iv. 68.)')).toBe('(Bd in iv. 68.)')
  })

  it('is off unless asked for', () => {
    expect(plainEntry(raw)).toContain('(S, Mgh, * Msb, K)')
    expect(laneEntry(raw)[0].senses[0].pieces.some((p) => p.text.includes('Msb'))).toBe(true)
  })

  it('tidies the set-out entry too, verses kept', () => {
    const text = laneEntry(`${raw} in the Kur [viii. 62] (TA.)`, { tidy: true })[0].senses[0].pieces
    const joined = text.map((p) => p.text).join('')
    expect(joined).not.toContain('Msb')
    expect(joined).not.toMatch(/\s[,.]/)
    expect(text.some((p) => p.kind === 'ref' && p.text === "Qur'án 8:62")).toBe(true)
  })

  it('starts each verb form on its own line in the prose view', () => {
    const said = plainEntry(`he did it. (TA.) 2 ${ar('شَرَّكَ')} see 4.`, { tidy: true })
    expect(said).toBe(`he did it.\n2 ${ar('شَرَّكَ')} see 4.`)
  })
})
