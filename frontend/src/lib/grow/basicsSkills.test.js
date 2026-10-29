import { describe, expect, it } from 'vitest'

import data from '../../../public/grow/basics.json'
import verbsData from '../../../public/grow/basics-verbs.json'
import worlds from '../../config/worlds.json'
import { INTRO, definite, keyOfBasic } from './alifLam'
import { DUAL, JOINED, MISSPELT, OBJECT_VERBS, OWNED, OWNERS, POINTED, SKILLS, THINGS, asksOf, basicsCards, markerAsks, pathItems, tableOf, teachMarker } from './basicsSkills'
import { makeRandom } from '../quiz/quiz'
import { isFeminine } from './nounForms'
import { canPossess, meanings, verbTable } from './wordForms'

const nfc = (text) => text.normalize('NFC')
const letters = (text) => text.replace(/[ً-ْٰ\s]/g, '')
const { words, path, people } = data
const { verbs, families } = verbsData
const items = pathItems(words, { verbs, families, people, path })
const itemOf = (id) => items.find((item) => item.id === id)
const markers = items.filter((item) => item.marker)
const book = words.find((word) => word.id === 'book')
const sun = words.find((word) => word.id === 'sun')

describe('pathItems', () => {
  const named = path.reduce((sum, step) => sum + (step.words ?? 0), 0)

  it('keeps the words the path names, once, in their order, with the id each always had', () => {
    const wordItems = items.filter((item) => !item.marker)
    expect(wordItems).toEqual(words.slice(0, named))
    expect(new Set(items.map(keyOfBasic)).size).toBe(items.length)
  })

  it('sets the skills between the words as the path says', () => {
    const skillAt = (id) => items.findIndex((item) => item.skill === id)
    expect(skillAt('mine')).toBe(10)
    expect(skillAt('people')).toBe(10 + 7 + 6)
    expect(skillAt('joined')).toBe(10 + 7 + 6 + 3 + 6)
    expect(items.slice(skillAt('past'), skillAt('past') + 7).map((item) => item.id)).toEqual(
      ['past:he', 'past:they', 'past:I', 'past:we', 'past:you', 'past:you-all', 'past:she'],
    )
    const order = [...new Set(markers.map((item) => item.skill))]
    expect(order).toEqual([
      'mine', 'people', 'joined', 'this', 'pronouns', 'of', 'two', 'past', 'present', 'object', 'negation', 'command', 'future', 'patterns',
    ])
    expect(markers).toHaveLength(Object.values(SKILLS).reduce((sum, skill) => sum + skill.markers.length, 0))
  })

  it('ends on a skill, not on a long run of ال words: ال is one rule', () => {
    expect(items.at(-1).marker).toBeTruthy()
    expect(named).toBeLessThan(words.length / 2)
  })

  it('gives a marker what its questions draw from', () => {
    expect(itemOf('past:she').words).toBe(verbs)
    expect(itemOf('mine:his').words.map((word) => word.id)).toEqual(OWNED)
    expect(itemOf('people:woman').words).toBe(people)
    expect(itemOf('joined:for').words.map((word) => word.id)).toEqual(JOINED)
    expect(itemOf('this:that').words.map((word) => word.id)).toEqual(POINTED)
    expect(itemOf('object:me').words.map((word) => word.id)).toEqual(OBJECT_VERBS)
    // A pattern draws only the families that have it.
    expect(itemOf('patterns:X').words.map((family) => family.id)).toEqual(['know', 'understand', 'write', 'open'])
    for (const item of markers.filter((one) => one.skill === 'patterns')) {
      expect(item.words.every((family) => family.forms[item.marker.key]), item.id).toBe(true)
    }
  })

  it('leaves out words the path does not name, and a path that names none is the old list', () => {
    expect(pathItems(words, { verbs, path: [] })).toEqual(words)
    expect(pathItems(words, { verbs, path: [{ words: 2 }, { skill: 'command' }] }).map((item) => item.id)).toEqual(
      ['book', 'sun', 'command:command', 'command:prohibit'],
    )
  })

  it('still gives the words when the verbs, the people or the path did not load (an older cached file, or offline)', () => {
    const older = pathItems(words, { verbs: null, families: null, people: undefined, path })
    expect(older.filter((item) => !item.marker)).toEqual(words.slice(0, named))
    expect(new Set(older.filter((item) => item.marker).map((item) => item.skill))).toEqual(new Set(['mine', 'joined', 'this', 'of', 'two']))
    expect(pathItems(words, { verbs })).toEqual(words)
    expect(pathItems(words, { verbs, path: [{ skill: 'gone' }] })).toEqual(words)
  })

  it('is as long as the last stage asks for', () => {
    const { stages } = worlds.worlds.find((world) => world.id === 'basics')
    expect(stages.at(-1)).toBe(items.length)
  })

  it('draws possessives only from nouns that take the endings plainly', () => {
    for (const id of OWNED) expect(canPossess(words.find((word) => word.id === id)), id).toBe(true)
  })

  it('finds every noun a skill names in the word list', () => {
    for (const id of [...OWNED, ...JOINED, ...POINTED]) expect(words.some((word) => word.id === id), id).toBe(true)
  })

  it('finds every thing, owner and pair of things the new noun skills name', () => {
    for (const id of [...OWNERS, ...THINGS, ...DUAL]) expect(words.some((word) => word.id === id), id).toBe(true)
    expect(itemOf('of:of').words).toHaveLength(OWNERS.length * THINGS.length)
    // لِـ joins the owner in “the book is the teacher’s”, so no owner starts with ل either.
    for (const id of OWNERS) expect(letters(words.find((word) => word.id === id).ar).startsWith('ل'), id).toBe(false)
    expect(itemOf('pronouns:he').words).toBe(people)
  })

  it('joins only words not starting with ل, which لِـ would spell another way (لِلَّيْل)', () => {
    for (const word of itemOf('joined:for').words) expect(letters(word.ar).startsWith('ل'), word.id).toBe(false)
  })

  // Feminine with no ة: هٰذِهِ شَمْس, so the ة cannot tell; these never go in POINTED.
  const FEMININE_WITHOUT_TA = ['sun', 'girl', 'mother', 'sister', 'hand', 'eye', 'ear', 'finger', 'desert', 'market', 'road', 'arm']
  it('points only at things whose gender the ة shows', () => {
    for (const id of FEMININE_WITHOUT_TA) expect(POINTED, id).not.toContain(id)
    const pointed = itemOf('this:this').words
    expect(pointed.some(isFeminine)).toBe(true)
    expect(pointed.some((word) => !isFeminine(word))).toBe(true)
  })

  it('draws people who take ة and the sound plurals, written as the rules say', () => {
    expect(new Set(people.map((one) => one.id)).size).toBe(people.length)
    for (const one of people) {
      expect(one.ar, one.id).toBe(nfc(one.ar))
      expect(letters(one.ar).endsWith('ة'), one.id).toBe(false)
      // Pausal: the last letter carries no vowel.
      expect(one.ar, one.id).not.toMatch(/[\u064B-\u0652]$/)
      expect(one.many, one.id).toMatch(/^[A-Za-z]+s$/)
    }
  })
})

describe('teachMarker', () => {
  it('shows the form on كَتَبَ, the form it changes, and the rule', () => {
    expect(teachMarker(itemOf('past:she'))).toEqual({
      kind: 'teach', id: 'teach:past:she', tag: 'The past', ar: nfc('كَتَبَتْ'), en: 'she wrote',
      also: { ar: nfc('كَتَبَ'), en: 'he wrote' }, note: SKILLS.past.markers.find((one) => one.id === 'she').rule,
    })
    expect(teachMarker(itemOf('negation:not-past'))).toMatchObject({ ar: nfc('لَمْ يَكْتُبْ'), en: 'he didn’t write', also: { ar: nfc('يَكْتُبُ') } })
    expect(teachMarker(itemOf('command:prohibit'))).toMatchObject({ ar: nfc('لَا تَكْتُبْ'), en: 'Don’t write! (one man)', also: { ar: nfc('اُكْتُبْ') } })
  })
  it('sets a man beside a woman, a word with ال beside one joined, and nothing beside “this is a …”', () => {
    expect(teachMarker(itemOf('people:woman'))).toMatchObject({ ar: nfc('مُسْلِمَة'), en: 'a Muslim (woman)', also: { ar: nfc('مُسْلِم'), en: 'a Muslim (man)' } })
    expect(teachMarker(itemOf('people:women'))).toMatchObject({ ar: nfc('مُسْلِمَات'), en: 'Muslims (women)', also: { ar: nfc('مُسْلِمَة') } })
    expect(teachMarker(itemOf('joined:for'))).toMatchObject({ ar: nfc('لِلْكِتَاب'), en: 'for the book', also: { ar: nfc('الْكِتَاب'), en: 'the book' } })
    expect(teachMarker(itemOf('this:this-is'))).toMatchObject({ ar: nfc('هٰذَا كِتَاب'), en: 'this is a book' })
    expect(teachMarker(itemOf('this:this-is')).also).toBeUndefined()
    expect(teachMarker(itemOf('this:that'))).toMatchObject({ ar: nfc('ذٰلِكَ الْكِتَاب'), en: 'that book', also: { ar: nfc('ذٰلِكَ كِتَاب') } })
  })
  it('sets the past beside “he heard him”, and form I beside a pattern', () => {
    expect(teachMarker(itemOf('object:him'))).toMatchObject({ ar: nfc('سَمِعَهُ'), en: 'he heard him', also: { ar: nfc('سَمِعَ'), en: 'he heard' } })
    expect(teachMarker(itemOf('patterns:V'))).toMatchObject({ tag: 'Verb patterns', ar: nfc('تَعَلَّمَ'), en: 'he learnt', also: { ar: nfc('عَلِمَ'), en: 'he knew' } })
    expect(teachMarker(itemOf('patterns:VI'))).toMatchObject({ ar: nfc('تَكَاتَبُوا'), en: 'they wrote to each other' })
  })
  it('sets the bare noun beside a possessive', () => {
    expect(teachMarker(itemOf('mine:my'))).toMatchObject({ ar: nfc('كِتَابِي'), en: 'my book', also: { ar: nfc('كِتَاب'), en: 'a book' } })
  })
  it('has nothing beside the past for “he”, the form the others grow from', () => {
    const card = teachMarker(itemOf('past:he'))
    expect(card.also).toBeUndefined()
    expect(card).toMatchObject({ ar: nfc('كَتَبَ'), en: 'he wrote' })
  })
})

describe('markerAsks', () => {
  it('asks a marker both ways, each on a verb and person of its own', () => {
    const [toArabic, toEnglish] = markerAsks(itemOf('past:she'), true, makeRandom(3))
    expect(toArabic).toMatchObject({ kind: 'choose', id: 'pick:past:she', tag: 'New form', arabic: true, answer: 'right' })
    expect(toArabic.ask).toMatch(/^Which one is “she .+”\?$/)
    expect(toArabic.options).toHaveLength(3)
    expect(toEnglish).toMatchObject({ id: 'read:past:she', ask: 'What does it mean?', answer: 'right' })
    expect(toEnglish.ar).toMatch(/تْ$/)
    expect(toEnglish.options.find((option) => option.id === 'right').text).toMatch(/^she /)
    expect(toArabic.record).toMatchObject({ module: 'basics', item: 'past:she', context: { world: 'basics', skill: 'past', direction: 'to-arabic' } })
    expect(toEnglish.record.context.direction).toBe('to-english')
    expect(toEnglish.record.context.word).toBe(toEnglish.ar)
    // Which verb and person were asked, so a later review can tell what a learner keeps missing.
    expect(verbs.map((verb) => verb.id)).toContain(toArabic.record.context.from)
    expect(toArabic.record.context.person).toBe('she')
    const [mine] = markerAsks(itemOf('mine:his'), true, makeRandom(3))
    expect(OWNED).toContain(mine.record.context.from)
    expect(mine.record.context).not.toHaveProperty('person')
    expect(markerAsks(itemOf('past:she'), false, makeRandom(3))[0].tag).toBe('Review')
  })

  it('says why: the right pair, then the rule', () => {
    const [card] = markerAsks(itemOf('future:future'), true, makeRandom(1))
    const right = card.options.find((option) => option.id === 'right').text
    expect(card.why).toBe(`${right} = ${card.ask.match(/“(.+)”/)[1]}. ${SKILLS.future.markers[0].rule}`)
  })

  it('tells a wrong pick what it picked: another form and its meaning, or the misspelling', () => {
    const seen = new Set()
    for (let seed = 1; seed <= 60; seed += 1) {
      for (const card of markerAsks(itemOf('mine:his'), true, makeRandom(seed))) {
        const said = card.why.slice(0, card.why.indexOf('.') + 1)
        const wrongIds = card.options.filter((option) => option.id !== 'right').map((option) => option.id)
        expect(Object.keys(card.wrong).sort()).toEqual(wrongIds.sort())
        for (const [id, line] of Object.entries(card.wrong)) {
          expect(line.startsWith(`${said} `)).toBe(true)
          const kind = id.startsWith('wrong:al:') ? 'al' : id.startsWith('wrong:ta:') ? 'ta' : 'form'
          seen.add(kind)
          if (kind === 'al') expect(line).toMatch(/never takes ال as well\.$/)
          if (kind === 'ta') expect(line).toMatch(/A final ة is written ت before an ending\.$/)
          if (kind === 'form') expect(line).toMatch(/ is “.+”\. ـهُ on the end means “his”\.$/)
        }
        // The ة half of the rule only where the word has a ة to change.
        const word = itemOf('mine:his').words.find((one) => one.id === card.record.context.from)
        expect(card.why.includes('ة is written ت'), word.ar).toBe(letters(word.ar).endsWith('ة'))
      }
    }
    expect([...seen].sort()).toEqual(['al', 'form', 'ta'])
  })

  it('draws different verbs and persons across lessons (the addition is learnt, not one word)', () => {
    const asked = new Set()
    const persons = new Set()
    for (let seed = 1; seed <= 40; seed += 1) {
      const [card] = markerAsks(itemOf('negation:not-past'), true, makeRandom(seed))
      asked.add(letters(card.options.find((option) => option.id === 'right').text))
      persons.add(card.ask.match(/“(\S+)/)[1])
    }
    expect(asked.size).toBeGreaterThan(15)
    expect(persons.size).toBeGreaterThanOrEqual(5)
  })

  it('never offers the plain present as wrong for “will”, since it can say will too, but does for reading سَ', () => {
    for (const id of ['future:future', 'future:future-sawfa']) {
      for (let seed = 1; seed <= 40; seed += 1) {
        const [toArabic, toEnglish] = markerAsks(itemOf(id), true, makeRandom(seed))
        const word = verbs.find((verb) => verb.id === toArabic.record.context.from)
        const table = verbTable(word)
        const presents = new Set(table.filter((entry) => entry.key.startsWith('present:')).map((entry) => entry.ar))
        for (const option of toArabic.options) expect(presents.has(option.text), `${id} ${option.text}`).toBe(false)
        expect(toEnglish.options.length).toBe(3)
      }
    }
    const offered = new Set()
    for (let seed = 1; seed <= 40; seed += 1) for (const option of markerAsks(itemOf('future:future'), true, makeRandom(seed))[1].options) offered.add(option.id.split(':')[0])
    expect(offered).toContain('present')
  })

  it('asks a command of the two “you” persons only', () => {
    for (let seed = 1; seed <= 20; seed += 1) {
      const [, card] = markerAsks(itemOf('command:command'), true, makeRandom(seed))
      expect(card.options.find((option) => option.id === 'right').text).toMatch(/!\s\((one man|all of you)\)$/)
    }
  })
})

describe('every marker, on every verb or noun and person (F2–F4)', () => {
  const tableFor = (item, word) => tableOf(item.skill, word)

  it.each(markers.map((item) => [item.id, item]))('%s: three options, one right, none of the wrong ones right too', (_, item) => {
    for (let seed = 1; seed <= 25; seed += 1) {
      for (const card of asksOf(item, true, makeRandom(seed))) {
        const texts = card.options.map((option) => option.text)
        expect(card.options, card.id).toHaveLength(3)
        expect(new Set(texts).size).toBe(3)
        expect(card.options.filter((option) => option.id === 'right')).toHaveLength(1)
        const right = card.options.find((option) => option.id === 'right').text
        // Every option is the same word: its root letters (or the noun's) are in each.
        const word = item.words.find((one) => {
          const table = tableFor(item, one)
          return table.some((entry) => entry.ar === (card.arabic ? right : card.ar))
        })
        expect(word, card.id).toBeTruthy()
        const table = tableFor(item, word)
        const byAr = meanings(table)
        if (card.arabic) {
          const core = word.root ? null : letters(word.ar).replace(/ة$/, '')
          for (const option of card.options) {
            if (core) expect(letters(option.text)).toContain(core)
            else expect(letters(option.text)).toMatch(new RegExp([...word.root].join('.*')))
            if (option.id !== 'right') expect(byAr.get(option.text).has(card.ask.match(/“(.+)”/)[1])).toBe(false)
          }
        } else {
          for (const option of card.options) if (option.id !== 'right') expect(byAr.get(card.ar).has(option.text)).toBe(false)
        }
      }
    }
  })

  it.each(markers.map((item) => [item.id, item]))('%s: says why for every wrong pick, never “undefined”', (_, item) => {
    for (let seed = 1; seed <= 25; seed += 1) {
      for (const card of asksOf(item, true, makeRandom(seed))) {
        expect(Object.keys(card.wrong).sort(), card.id).toEqual(card.options.filter((one) => one.id !== 'right').map((one) => one.id).sort())
        for (const line of Object.values(card.wrong)) expect(line, card.id).not.toMatch(/undefined|null/)
      }
    }
  })

  it('has a line for every kind of misspelling a table can make', () => {
    const kinds = new Set()
    for (const item of markers) {
      for (const word of item.words) {
        for (const entry of tableOf(item.skill, word)) if (entry.key.startsWith('wrong:')) kinds.add(entry.key.split(':')[1])
      }
    }
    expect([...kinds].sort()).toEqual(Object.keys(MISSPELT).sort())
  })

  it('never sets the prohibition for one man beside لا with the plain present', () => {
    const not = verbTable(verbs[0]).find((entry) => entry.key === 'not:you')
    for (let seed = 1; seed <= 25; seed += 1) {
      for (const card of markerAsks(itemOf('command:prohibit'), true, makeRandom(seed))) {
        expect(card.options.map((option) => option.text)).not.toContain(not.ar)
        expect(card.options.map((option) => option.text)).not.toContain(not.en)
      }
    }
  })
})

describe('SKILLS', () => {
  it('names each skill as its teach cards show it', () => {
    expect(Object.entries(SKILLS).map(([id, skill]) => [id, skill.title, skill.table])).toEqual([
      ['mine', 'My, his, her', 'nouns'], ['people', 'One and many', 'people'], ['joined', 'And, with, for, like', 'joined'],
      ['this', 'This, that', 'pointing'], ['pronouns', 'He, she, I', 'pronouns'], ['of', 'The … of …', 'pairs'], ['two', 'Two', 'dual'],
      ['past', 'The past', 'verbs'], ['present', 'The present', 'verbs'],
      ['negation', 'Not', 'verbs'], ['command', 'Do! Don’t!', 'verbs'], ['future', 'Will', 'verbs'],
      ['object', 'Him, her, me', 'objects'], ['patterns', 'Verb patterns', 'families'],
    ])
  })

  // Every key a marker names (its own, its base, its pools) is a form the table has, for every person it draws.
  it.each(markers.filter((item) => !SKILLS[item.skill].asks).map((item) => [item.id, item]))('%s: every form it names is in the table', (_, item) => {
    const { table, markers: all } = SKILLS[item.skill]
    const word = item.words[0]
    const keys = new Set(tableOf(item.skill, ['nouns', 'dual'].includes(table) ? { ...word, ar: 'مَدْرَسَة' } : word).map((entry) => entry.key))
    const { key, base, persons, pool, toEnglish = [] } = item.marker
    expect(all).toContain(item.marker)
    for (const person of persons) {
      const at = (one) => one.replace('{p}', person)
      for (const one of [key, ...pool, ...toEnglish]) expect(keys.has(at(one)), `${at(one)}`).toBe(true)
      if (base && base !== 'bare') expect(keys.has(at(base)), at(base)).toBe(true)
      expect(pool.filter((one) => keys.has(at(one)) && at(one) !== at(key)).length).toBeGreaterThanOrEqual(2)
    }
  })

  it('says “my, his, her” on nouns for anyone, and each verb marker for the persons it is said by', () => {
    expect(SKILLS.mine.markers.every((marker) => marker.persons.length === 1 && marker.persons[0] === null && marker.base === 'bare')).toBe(true)
    for (const skill of ['people', 'joined', 'this']) expect(SKILLS[skill].markers.every((marker) => marker.persons[0] === null)).toBe(true)
    expect(SKILLS.past.markers.map((marker) => marker.persons)).toEqual([['he'], ['they'], ['I'], ['we'], ['you'], ['you-all'], ['she']])
    expect(SKILLS.command.markers.map((marker) => marker.persons)).toEqual([['you', 'you-all'], ['you', 'you-all']])
    for (const skill of ['negation', 'future']) for (const marker of SKILLS[skill].markers) expect(marker.persons).toEqual(['he', 'she', 'they', 'you', 'you-all', 'I', 'we'])
  })

  // What each rule teaches: the addition, then what it says in English.
  const TAUGHT = {
    'mine:my': ['ـِي', '“my”'], 'mine:his': ['ـهُ', '“his”'], 'mine:her': ['ـهَا', '“her”'], 'mine:our': ['ـنَا', '“our”'],
    'mine:their': ['ـهُمْ', '“their”'], 'mine:your': ['ـكَ', 'one man'], 'mine:your-all': ['ـكُمْ', 'a group'],
    'people:woman': ['ة', 'woman'], 'people:men': ['ـُونَ', 'men', 'ـِينَ'], 'people:women': ['ـَات', 'women'],
    'joined:and': ['وَ', 'and'], 'joined:with': ['بِـ', 'with'], 'joined:for': ['لِـ', 'for', 'ا is dropped'], 'joined:like': ['كَـ', 'like'],
    'object:him': ['ـهُ', 'him'], 'object:her': ['ـهَا', 'her'], 'object:them': ['ـهُمْ', 'them'], 'object:me': ['ـنِي', 'me', 'my'],
    'object:us': ['ـنَا', 'us', 'we heard'], 'object:you': ['ـكَ', 'one man'], 'object:you-all': ['ـكُمْ', 'a group'],
    'patterns:II': ['فَعَّلَ', 'making someone do it'], 'patterns:III': ['فَاعَلَ', 'with or to someone'], 'patterns:IV': ['أَفْعَلَ', 'making someone do it'],
    'patterns:V': ['تَفَعَّلَ', 'back on the doer'], 'patterns:VI': ['تَفَاعَلَ', 'each other'], 'patterns:VII': ['اِنْفَعَلَ', 'by itself'],
    'patterns:VIII': ['اِفْتَعَلَ', 'for yourself'], 'patterns:X': ['اِسْتَفْعَلَ', 'asking for it'],
    'pronouns:he': ['هُوَ', '“is”'], 'pronouns:she': ['هِيَ', 'ة'], 'pronouns:they': ['هُمْ', 'ـُونَ'], 'pronouns:I': ['أَنَا', 'a woman'],
    'pronouns:we': ['نَحْنُ', 'we'], 'pronouns:you': ['أَنْتَ', 'one man'], 'pronouns:you-woman': ['أَنْتِ', 'one woman'], 'pronouns:you-all': ['أَنْتُمْ', 'a group'],
    'of:of': ['“the … of …”', 'never takes ال', 'كِتَابُ اللهِ'], 'of:a': ['no ال', '“a”'],
    'two:two': ['ـَانِ', 'two', 'ـَيْنِ', 'ت'], 'two:the-two': ['ال', 'the two'],
    'this:this-is': ['هٰذَا', 'this is', 'هٰذِهِ'], 'this:this': ['ال', '“this”'], 'this:that-is': ['ذٰلِكَ', 'تِلْكَ'], 'this:that': ['ال', '“that”'],
    'past:he': ['كَتَبَ', 'he wrote'], 'past:they': ['ـُوا', 'they did'], 'past:I': ['ـْتُ', 'I did'], 'past:we': ['ـْنَا', 'we did'],
    'past:you': ['ـْتَ', 'one man'], 'past:you-all': ['ـْتُمْ', 'you all did'], 'past:she': ['ـَتْ', 'she did'],
    'present:he': ['يَـ', 'he writes'], 'present:she': ['تَـ', 'she'], 'present:they': ['ـُونَ', 'they'], 'present:I': ['أَ', 'I'],
    'present:we': ['نَ', 'we'], 'present:you': ['تَـ', 'one man'], 'present:you-all': ['ـُونَ', 'you all'],
    'negation:not': ['لَا', 'doesn’t'], 'negation:not-past': ['لَمْ', 'didn’t'], 'negation:not-future': ['لَنْ', 'won’t'],
    'negation:not-past-ma': ['مَا', 'didn’t'], 'command:command': ['اُكْتُبْ', 'drops “you”'], 'command:prohibit': ['لَا', 'Don’t'],
    'future:future': ['سَ', 'will'], 'future:future-sawfa': ['سَوْفَ', 'will'],
  }
  it('teaches every marker, and no other', () => expect(markers.map((item) => item.id).sort()).toEqual(Object.keys(TAUGHT).sort()))
  it.each(Object.entries(TAUGHT))('%s: its rule names the addition and what it says', (id, said) => {
    const { rule } = itemOf(id).marker
    for (const one of said) expect(rule).toContain(one)
    if (id.startsWith('mine:')) expect(rule).toMatch(/never takes ال as well, and a final ة is written ت before it\.$/)
  })
})

describe('rules', () => {
  // A vowel mark alone, after a space or quote, draws on a dotted circle or on the letter before it: it sits on ـ.
  it.each(markers.map((item) => [item.id, item.marker.rule]))('%s: no mark stands alone', (_, rule) => {
    expect(rule).not.toMatch(/(?:^|[\s"“‘(,.])[\u064B-\u0652]/)
  })
})

describe('basicsCards', () => {
  it('opens a first lesson on what ال is, then teaches each new item and asks it both ways', () => {
    const cards = basicsCards({ fresh: [book, itemOf('mine:my')], reviews: [] }, makeRandom(2), true)
    expect(cards.map((card) => card.id)).toEqual(['teach:al', 'teach:book', 'the:book', 'means:book', 'teach:mine:my', 'pick:mine:my', 'read:mine:my'])
    expect(cards[0]).toBe(INTRO)
    expect(cards[1]).toMatchObject({ ar: definite('كِتَاب'), en: 'the book' })
  })
  it('does not open a later lesson on it, and asks a review with no teach card', () => {
    const cards = basicsCards({ fresh: [sun], reviews: [itemOf('past:I')] }, makeRandom(2))
    expect(cards.map((card) => card.id)).toEqual(['teach:sun', 'the:sun', 'means:sun', 'pick:past:I', 'read:past:I'])
    expect(cards.at(-1).tag).toBe('Review')
  })
})
