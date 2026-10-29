import { describe, expect, it } from 'vitest'

import basics from '../../../public/grow/basics.json'
import data from '../../../public/grow/basics-verbs.json'
import { makeRandom } from '../quiz/quiz'
import {
  ADDRESSED, PERSONS, POSSESSORS, TENSES, WRONG_VERB, arabicOptions, canPossess, englishOptions, meanings, objectTable,
  possessiveTable, questionTable, relativeTable, verbTable,
} from './wordForms'

const nfc = (text) => text.normalize('NFC')
const write = data.verbs.find((verb) => verb.id === 'write')
const table = verbTable(write)
const at = (entries, key) => entries.find((entry) => entry.key === key)
const book = { id: 'book', ar: 'كِتَاب', en: 'book' }
const school = { id: 'school', ar: 'مَدْرَسَة', en: 'school' }

describe('PERSONS', () => {
  it('is the data file’s seven, in its order', () => {
    expect(PERSONS.map((person) => person.id)).toEqual(data.persons)
    expect(ADDRESSED.every((id) => data.persons.includes(id))).toBe(true)
  })
})

describe('verbTable', () => {
  it('puts each particle where it goes', () => {
    const say = (key) => [at(table, key).ar, at(table, key).en]
    expect(say('past:she')).toEqual([nfc('كَتَبَتْ'), 'she wrote'])
    expect(say('past:you')).toEqual([nfc('كَتَبْتَ'), 'you wrote (one man)'])
    expect(say('past:you-all')).toEqual([nfc('كَتَبْتُمْ'), 'you all wrote'])
    expect(say('present:he')).toEqual([nfc('يَكْتُبُ'), 'he writes'])
    expect(say('present:she')).toEqual([nfc('تَكْتُبُ'), 'she writes'])
    expect(say('present:they')).toEqual([nfc('يَكْتُبُونَ'), 'they write'])
    expect(say('present:I')).toEqual([nfc('أَكْتُبُ'), 'I write'])
    expect(say('future:we')).toEqual([nfc('سَنَكْتُبُ'), 'we will write'])
    expect(say('future-sawfa:he')).toEqual([nfc('سَوْفَ يَكْتُبُ'), 'he will write'])
    expect(say('not:he')).toEqual([nfc('لَا يَكْتُبُ'), 'he doesn’t write'])
    expect(say('not:they')).toEqual([nfc('لَا يَكْتُبُونَ'), 'they don’t write'])
    expect(say('not-past:he')).toEqual([nfc('لَمْ يَكْتُبْ'), 'he didn’t write'])
    expect(say('not-past:they')).toEqual([nfc('لَمْ يَكْتُبُوا'), 'they didn’t write'])
    expect(say('not-past-ma:he')).toEqual([nfc('مَا كَتَبَ'), 'he didn’t write'])
    expect(say('not-future:he')).toEqual([nfc('لَنْ يَكْتُبَ'), 'he won’t write'])
    expect(say('not-future:you-all')).toEqual([nfc('لَنْ تَكْتُبُوا'), 'you all won’t write'])
    expect(say('command:you')).toEqual([nfc('اُكْتُبْ'), 'Write! (one man)'])
    expect(say('command:you-all')).toEqual([nfc('اُكْتُبُوا'), 'Write! (all of you)'])
    expect(say('prohibit:you')).toEqual([nfc('لَا تَكْتُبْ'), 'Don’t write! (one man)'])
    expect(say('prohibit:you-all')).toEqual([nfc('لَا تَكْتُبُوا'), 'Don’t write! (all of you)'])
  })

  it('builds the wrong forms, with no meaning', () => {
    const wrong = (key) => at(table, key)
    expect(wrong('wrong:sa-past:he')).toEqual({ key: 'wrong:sa-past:he', ar: nfc('سَكَتَبَ'), en: null })
    expect(wrong('wrong:sa-apart:he').ar).toBe(nfc('سَ يَكْتُبُ'))
    expect(wrong('wrong:sawfa-past:he').ar).toBe(nfc('سَوْفَ كَتَبَ'))
    expect(wrong('wrong:lam-past:he').ar).toBe(nfc('لَمْ كَتَبَ'))
    expect(wrong('wrong:lan-past:she').ar).toBe(nfc('لَنْ كَتَبَتْ'))
  })

  it('gives commands to the two “you” persons only', () => {
    const keys = table.map((entry) => entry.key)
    expect(keys.filter((key) => /^(command|prohibit):/.test(key)).sort()).toEqual(
      ['command:you', 'command:you-all', 'prohibit:you', 'prohibit:you-all'],
    )
    const each = Object.keys(TENSES).length - 2 + Object.keys(WRONG_VERB).length
    expect(table).toHaveLength(PERSONS.length * each + 2 * ADDRESSED.length)
  })

  it('uses the third-person English for he and she only, and keeps a two-word verb whole', () => {
    const thank = verbTable(data.verbs.find((verb) => verb.id === 'thank'))
    expect(at(thank, 'present:she').en).toBe('she gives thanks')
    expect(at(thank, 'present:we').en).toBe('we give thanks')
    expect(at(thank, 'not:she').en).toBe('she doesn’t give thanks')
    expect(at(thank, 'not:I').en).toBe('I don’t give thanks')
    expect(at(thank, 'past:I').en).toBe('I gave thanks')
    expect(at(thank, 'command:you').en).toBe('Give thanks! (one man)')
  })

  it('is normalised, so equal spellings compare equal', () => {
    for (const verb of data.verbs) for (const { ar } of verbTable(verb)) expect(ar).toBe(nfc(ar))
  })
})

describe('meanings', () => {
  it('collects every reading of one spelling', () => {
    const byAr = meanings(table)
    expect([...byAr.get(nfc('تَكْتُبُ'))].sort()).toEqual(['she writes', 'you write (one man)'])
    expect([...byAr.get(nfc('لَمْ تَكْتُبْ'))].sort()).toEqual(['she didn’t write', 'you didn’t write (one man)'])
    expect([...byAr.get(nfc('سَكَتَبَ'))]).toEqual([])
  })
})

describe('canPossess', () => {
  it('takes words ending on a plain consonant or ة', () => {
    expect(canPossess(book)).toBe(true)
    expect(canPossess(school)).toBe(true)
    expect(canPossess({ ar: 'يَد' })).toBe(true)
  })
  it('leaves out long vowels, hamza, doubled letters and the lengthening nouns', () => {
    for (const ar of ['كُرْسِيّ', 'أُمّ', 'صَحْرَاء', 'مُسْتَشْفَى', 'ظَبْي', 'عَصَا', 'دَلْو', 'أَب', 'أَخ', 'شَيْءٌ']) {
      expect(canPossess({ ar }), ar).toBe(false)
    }
  })
  it('reads past tanween', () => {
    expect(canPossess({ ar: 'كِتَابٌ' })).toBe(true)
  })
})

describe('possessiveTable', () => {
  it('joins each ending to the noun', () => {
    const mine = possessiveTable(book)
    expect(at(mine, 'mine:my')).toEqual({ key: 'mine:my', ar: nfc('كِتَابِي'), en: 'my book' })
    expect(at(mine, 'mine:your').en).toBe('your book (one man)')
    expect(at(mine, 'mine:your').ar).toBe(nfc('كِتَابُكَ'))
    expect(at(mine, 'mine:his').ar).toBe(nfc('كِتَابُهُ'))
    expect(at(mine, 'mine:her').ar).toBe(nfc('كِتَابُهَا'))
    expect(at(mine, 'mine:our').ar).toBe(nfc('كِتَابُنَا'))
    expect(at(mine, 'mine:your-all')).toEqual({ key: 'mine:your-all', ar: nfc('كِتَابُكُمْ'), en: 'your book (all of you)' })
    expect(at(mine, 'mine:their').ar).toBe(nfc('كِتَابُهُمْ'))
    expect(POSSESSORS.map((owner) => at(mine, `mine:${owner.id}`).en)).toEqual(
      ['my book', 'your book (one man)', 'his book', 'her book', 'our book', 'your book (all of you)', 'their book'],
    )
    expect(at(mine, 'wrong:al:his')).toEqual({ key: 'wrong:al:his', ar: nfc('الْكِتَابُهُ'), en: null })
    expect(at(mine, 'wrong:ta:his')).toBeUndefined()
    // ال with ـِي could read as a real word (الْكِتَابِي, like الْجَارِي the flowing), so that one is not offered.
    expect(at(mine, 'wrong:al:my')).toBeUndefined()
    expect(mine).toHaveLength(2 * POSSESSORS.length - 1)
  })
  it('writes ة as ت before the ending, and keeps the wrong ة as a wrong form', () => {
    const mine = possessiveTable(school)
    expect(at(mine, 'mine:my').ar).toBe(nfc('مَدْرَسَتِي'))
    expect(at(mine, 'mine:her').ar).toBe(nfc('مَدْرَسَتُهَا'))
    expect(at(mine, 'wrong:ta:his').ar).toBe(nfc('مَدْرَسَةُهُ'))
    expect(at(mine, 'wrong:al:his').ar).toBe(nfc('الْمَدْرَسَتُهُ'))
    expect(mine).toHaveLength(3 * POSSESSORS.length)
  })
  it('follows ال’s sun-letter spelling in the wrong form', () => {
    expect(at(possessiveTable({ ar: 'شَمْس', en: 'sun' }), 'wrong:al:his').ar).toBe(nfc('الشَّمْسُهُ'))
    expect(at(possessiveTable({ ar: 'سَيَّارَة', en: 'car' }), 'wrong:al:my').ar).toBe(nfc('السَّيَّارَتِي'))
  })
})

describe('objectTable', () => {
  const hear = data.verbs.find((verb) => verb.id === 'hear')
  it('joins him, her, me… to the past for “he”', () => {
    const entries = objectTable(hear)
    expect(at(entries, 'him')).toMatchObject({ ar: nfc('سَمِعَهُ'), en: 'he heard him' })
    expect(at(entries, 'me')).toMatchObject({ ar: nfc('سَمِعَنِي'), en: 'he heard me' })
    expect(at(entries, 'you')).toMatchObject({ ar: nfc('سَمِعَكَ'), en: 'he heard you (one man)' })
    expect(at(entries, 'you-all')).toMatchObject({ ar: nfc('سَمِعَكُمْ'), en: 'he heard you (all of you)' })
  })
  it('sets “he heard us” beside “we heard”, one mark apart, and ـِي for me with no meaning', () => {
    const entries = objectTable(hear)
    expect(at(entries, 'us').ar).toBe(nfc('سَمِعَنَا'))
    expect(at(entries, 'we')).toMatchObject({ ar: nfc('سَمِعْنَا'), en: 'we heard' })
    expect(at(entries, 'wrong:ya:me')).toEqual({ key: 'wrong:ya:me', ar: nfc('سَمِعِي'), en: null })
  })
})

describe('relativeTable', () => {
  it('sets الَّذِي, الَّتِي and الَّذِينَ before the verb for their person', () => {
    const entries = relativeTable(write)
    expect(at(entries, 'the-man')).toMatchObject({ ar: nfc('الَّذِي كَتَبَ'), en: 'the man who wrote' })
    expect(at(entries, 'the-woman')).toMatchObject({ ar: nfc('الَّتِي كَتَبَتْ'), en: 'the woman who wrote' })
    expect(at(entries, 'those')).toMatchObject({ ar: nfc('الَّذِينَ كَتَبُوا'), en: 'those who wrote' })
    expect(at(entries, 'the-man-now')).toMatchObject({ ar: nfc('الَّذِي يَكْتُبُ'), en: 'the man who writes' })
    expect(at(entries, 'those-now')).toMatchObject({ ar: nfc('الَّذِينَ يَكْتُبُونَ'), en: 'those who write' })
  })
  it('never pairs one with another person’s verb, which would say “that which…”', () => {
    for (const verb of data.verbs) expect(relativeTable(verb).some((entry) => entry.ar.startsWith(nfc('الَّذِي ')) && entry.ar.includes(verb.forms.she.past))).toBe(false)
  })
})

describe('questionTable', () => {
  const entries = questionTable(write)
  it('asks with هَلْ or أَ before the past, هَلْ before the present, and مَنْ, مَاذَا, أَيْنَ', () => {
    expect(at(entries, 'did:he')).toMatchObject({ ar: nfc('هَلْ كَتَبَ؟'), en: 'did he write?' })
    expect(at(entries, 'a-did:he')).toMatchObject({ ar: nfc('أَكَتَبَ؟'), en: 'did he write?' })
    expect(at(entries, 'does:they')).toMatchObject({ ar: nfc('هَلْ يَكْتُبُونَ؟'), en: 'do they write?' })
    expect(at(entries, 'does:she').en).toBe('does she write?')
    expect(at(entries, 'who')).toMatchObject({ ar: nfc('مَنْ كَتَبَ؟'), en: 'who wrote?' })
    expect(at(entries, 'what:you')).toMatchObject({ ar: nfc('مَاذَا كَتَبْتَ؟'), en: 'what did you write (one man)?' })
    expect(at(entries, 'where:we')).toMatchObject({ ar: nfc('أَيْنَ كَتَبْنَا؟'), en: 'where did we write?' })
    expect(at(entries, 'said:she')).toMatchObject({ ar: nfc('كَتَبَتْ'), en: 'she wrote' })
  })
  it('writes أَ apart only as the mistake, with no meaning', () => {
    expect(at(entries, 'wrong:apart:he')).toEqual({ key: 'wrong:apart:he', ar: nfc('أَ كَتَبَ؟'), en: null })
    expect(at(entries, 'who:she')).toBeUndefined()
  })
})

describe('the option pickers', () => {
  const keys = (entries) => entries.map((entry) => entry.key)

  it('offer the asked form and n wrong ones, each once', () => {
    const options = arabicOptions(table, 'past:she', keys(table), makeRandom(1))
    expect(options).toHaveLength(3)
    expect(options.filter((option) => option.id === 'right')).toEqual([{ id: 'right', text: nfc('كَتَبَتْ') }])
    expect(new Set(options.map((option) => option.text)).size).toBe(3)
    expect(arabicOptions(table, 'past:she', keys(table), makeRandom(1), 4)).toHaveLength(5)
    const english = englishOptions(table, 'future:he', keys(table), makeRandom(2))
    expect(english).toHaveLength(3)
    expect(english.find((option) => option.id === 'right').text).toBe('he will write')
    expect(new Set(english.map((option) => option.text)).size).toBe(3)
  })

  it('take wrong options from the pool only, and skip keys not in the table', () => {
    const options = arabicOptions(table, 'past:she', ['past:he', 'nope'], makeRandom(3))
    expect(options.map((option) => option.id).sort()).toEqual(['past:he', 'right'])
    const english = englishOptions(table, 'past:she', ['past:he', 'wrong:sa-past:he', 'nope'], makeRandom(3))
    expect(english.map((option) => option.id).sort()).toEqual(['past:he', 'right'])
  })

  it('never offer, as wrong, a spelling that can also mean what was asked', () => {
    // تَكْتُبُ is "you write" too, and لَمْ يَكْتُبْ says what مَا كَتَبَ says.
    const options = arabicOptions(table, 'present:she', ['present:you', 'present:he'], makeRandom(4))
    expect(options.map((option) => option.id).sort()).toEqual(['present:he', 'right'])
    const ma = arabicOptions(table, 'not-past-ma:he', ['not-past:he', 'not:he'], makeRandom(4))
    expect(ma.map((option) => option.id).sort()).toEqual(['not:he', 'right'])
    const shown = englishOptions(table, 'present:you', ['present:she', 'present:I'], makeRandom(4))
    expect(shown.map((option) => option.id).sort()).toEqual(['present:I', 'right'])
    const same = englishOptions(table, 'future:he', ['future-sawfa:he', 'present:he'], makeRandom(4))
    expect(same.map((option) => option.id).sort()).toEqual(['present:he', 'right'])
  })

  it('show one wrong meaning once, though two forms carry it', () => {
    const english = englishOptions(table, 'present:he', ['not-past:he', 'not-past-ma:he'], makeRandom(5))
    expect(english.map((option) => option.text).sort()).toEqual(['he didn’t write', 'he writes'])
  })

  it('order the options by the generator', () => {
    const one = arabicOptions(table, 'past:she', keys(table), makeRandom(7))
    expect(arabicOptions(table, 'past:she', keys(table), makeRandom(7))).toEqual(one)
    const seen = new Set()
    for (let seed = 1; seed < 30; seed += 1) seen.add(arabicOptions(table, 'past:she', keys(table), makeRandom(seed)).findIndex((o) => o.id === 'right'))
    expect(seen.size).toBe(3)
  })
})

describe('no wrong option is ever right (F3), over every verb, form and pool', () => {
  const sayable = (entries) => entries.filter((entry) => entry.en)
  const tables = [
    ...data.verbs.map((verb) => [verb.id, verbTable(verb)]),
    ...basics.words.filter(canPossess).map((word) => [word.id, possessiveTable(word)]),
  ]

  it.each(tables)('%s', (_, entries) => {
    const byAr = meanings(entries)
    const pool = entries.map((entry) => entry.key)
    for (const asked of sayable(entries)) {
      for (let seed = 1; seed <= 3; seed += 1) {
        for (const option of arabicOptions(entries, asked.key, pool, makeRandom(seed), 6)) {
          if (option.id !== 'right') expect(byAr.get(option.text).has(asked.en), `${asked.key} ← ${option.text}`).toBe(false)
        }
        const readings = byAr.get(asked.ar)
        for (const option of englishOptions(entries, asked.key, pool, makeRandom(seed), 6)) {
          if (option.id !== 'right') expect(readings.has(option.text), `${asked.key} ← ${option.text}`).toBe(false)
        }
      }
    }
  })

  it('and the possessive table covers most of the Basics nouns', () => {
    expect(basics.words.filter(canPossess).length).toBeGreaterThan(100)
  })
})
