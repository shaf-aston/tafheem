import { describe, expect, it } from 'vitest'

import cuts from '../../public/words/cuts.json'
import words from '../../public/words/words.json'
import { buildQuestion, DIRECTIONS, makeRandom, pickDistractors } from './quiz'

// The everyday set as it actually ships, one row per word, with its topic and
// its type on it, rather than the list file it was authored in.
const BANK = cuts.everyday.map((at) => words.words[at])
const topicOf = (word) => word.groups[0]
const DIRECTION_IDS = Object.keys(DIRECTIONS)

// The everyday set ships with no Urdu; only the Qur'anic words have one. So an
// Urdu direction is exercised against the same rows with an Urdu meaning put on
// them, since what these cases check is the shape of a question, not the words.
// The words are reversed rather than copied, because Urdu closes a gloss where
// English opens it and a copy would leave every option ending the same way.
const URDU_BANK = BANK.map((word) => ({ ...word, ur: word.en.split(/\s+/).reverse().join(' ') }))
const bankFor = (direction) => (
  DIRECTIONS[direction].promptKey === 'ur' || DIRECTIONS[direction].answerKey === 'ur' ? URDU_BANK : BANK
)

/** Every question the bank can currently produce, so claims below cover all of it. */
const everyQuestion = (direction) =>
  Array.from({ length: 200 }, (_, seed) =>
    buildQuestion(bankFor(direction), { direction, random: makeRandom(seed + 1) }),
  )

describe('the word bank', () => {
  it('gives every entry an Arabic word, a meaning, a topic and a type', () => {
    for (const word of BANK) {
      expect(word.ar, JSON.stringify(word)).toBeTruthy()
      expect(word.en, JSON.stringify(word)).toBeTruthy()
      expect(word.meaningKey, JSON.stringify(word)).toBeTruthy()
      expect(word.groups, JSON.stringify(word)).toHaveLength(1)
      expect(['noun', 'verb', 'adjective'], JSON.stringify(word)).toContain(word.wordType)
    }
  })

  it('never spells two different words the same way', () => {
    // Two rows both reading كِتاب would make an Arabic-to-English question
    // unanswerable however the options fall. Two rows both meaning "cat" would
    // not: فَم and فُو are two real words, they share a meaning key, and the
    // rule below is what stops both being offered at once.
    expect(new Set(BANK.map((w) => w.ar)).size).toBe(BANK.length)
  })
})

describe.each(DIRECTION_IDS)('questions in the %s direction', (direction) => {
  const questions = everyQuestion(direction)

  it('offers four options', () => {
    for (const q of questions) expect(q.options).toHaveLength(4)
  })

  it('includes the right answer exactly once', () => {
    for (const q of questions) {
      const matches = q.options.filter((o) => o.id === q.answerId)
      expect(matches).toHaveLength(1)
      expect(matches[0].text).toBe(q.answerText)
    }
  })

  it('never shows two options that mean the same thing', () => {
    for (const q of questions) {
      const meanings = q.options.map((o) => o.id)
      expect(new Set(meanings).size, JSON.stringify(q)).toBe(meanings.length)
      const texts = q.options.map((o) => o.text)
      expect(new Set(texts).size, JSON.stringify(q)).toBe(texts.length)
    }
  })

  it('never puts the prompt itself among the answers', () => {
    for (const q of questions) {
      expect(q.options.map((o) => o.text)).not.toContain(q.prompt)
    }
  })

  it('does not always put the answer in the same slot', () => {
    const positions = new Set(
      questions.map((q) => q.options.findIndex((o) => o.id === q.answerId)),
    )
    expect(positions.size).toBeGreaterThan(1)
  })
})

describe('distractor choice', () => {
  // Anchored on the bank's busiest topic rather than one named word, so editing
  // the word list can never quietly turn these into tests of nothing.
  const perTopic = {}
  for (const w of BANK) perTopic[topicOf(w)] = (perTopic[topicOf(w)] ?? 0) + 1
  const busiest = Object.entries(perTopic).sort((a, b) => b[1] - a[1])[0][0]
  // Its own type as well as its own topic, so the type rule cannot thin the
  // topic out from under the test.
  const answer = BANK.find((w) => topicOf(w) === busiest && w.wordType === 'noun')

  it('prefers wrong options from the answer\'s own topic, so guessing by topic fails', () => {
    const distractors = pickDistractors(BANK, answer, 3, makeRandom(7))
    expect(distractors).toHaveLength(3)
    for (const d of distractors) expect(topicOf(d)).toBe(topicOf(answer))
  })

  it('reaches outside the topic rather than returning too few options', () => {
    const tinyTopic = [
      answer,
      { ...answer, en: 'only sibling', meaningKey: 'sibling-only' },
      { ...answer, en: 'far thing', groups: ['elsewhere'], meaningKey: 'far-1' },
      { ...answer, en: 'other thing', groups: ['elsewhere'], meaningKey: 'far-2' },
    ]
    const distractors = pickDistractors(tinyTopic, answer, 3, makeRandom(3))
    expect(distractors).toHaveLength(3)
  })

  it('drops a synonym of the answer instead of offering it as wrong', () => {
    const twin = { ...answer, en: 'the same thing' }
    const distractors = pickDistractors([...BANK, twin], answer, 3, makeRandom(11))
    expect(distractors.map((d) => d.en)).not.toContain(twin.en)
  })

  it('returns what it can when the bank is too small, rather than repeating a word', () => {
    const twoWords = [answer, { ...answer, en: 'lone', meaningKey: 'lone' }]
    const distractors = pickDistractors(twoWords, answer, 3, makeRandom(5))
    expect(distractors).toHaveLength(1)
  })

  // The whole-Qur'an bank has no topics, 4,450 words nobody grouped by hand; 
  // so the kind of word is the only thing keeping "argued" away from قَلَم.
  const noun = { ar: 'قَلَم', en: 'pen', meaningKey: 'pen', wordType: 'noun' }
  const untopiced = [
    noun,
    { ar: 'ـ', en: 'argued', meaningKey: 'argued', wordType: 'verb' },
    { ar: 'ـ', en: 'went', meaningKey: 'went', wordType: 'verb' },
    { ar: 'ـ', en: 'wrote', meaningKey: 'wrote', wordType: 'verb' },
    { ar: 'ـ', en: 'book', meaningKey: 'book', wordType: 'noun' },
    { ar: 'ـ', en: 'house', meaningKey: 'house', wordType: 'noun' },
    { ar: 'ـ', en: 'road', meaningKey: 'road', wordType: 'noun' },
  ]

  it('matches the kind of word when there is no topic to go on', () => {
    const distractors = pickDistractors(untopiced, noun, 3, makeRandom(9))
    expect(distractors.map((d) => d.wordType)).toEqual(['noun', 'noun', 'noun'])
  })

  // Rewritten: this used to assert that a shared topic could pull a verb in
  // beside a noun. It cannot any more, the kind of word is now a rule, and the
  // topic only orders the words that already passed it.
  it('orders by topic within one kind, and never reaches outside it', () => {
    const topical = [
      { ...noun, groups: ['school'] },
      { ar: 'ـ', en: 'teacher', meaningKey: 'teacher', wordType: 'noun', groups: ['school'] },
      { ar: 'ـ', en: 'wrote', meaningKey: 'wrote', wordType: 'verb', groups: ['school'] },
      { ar: 'ـ', en: 'mountain', meaningKey: 'mountain', wordType: 'noun', groups: ['nature'] },
    ]
    const distractors = pickDistractors(topical, topical[0], 2, makeRandom(4))
    // Both nouns, and the one sharing the answer's topic is offered first.
    expect(distractors.map((d) => d.en)).toEqual(['teacher', 'mountain'])
  })

  // The case a preference-only sort got wrong, and the reason it was never
  // caught: surah 9 is big enough to always have three of every kind, but 26 of
  // the 114 surah word lists are not.
  it('asks a shorter question rather than reach for another kind', () => {
    const thin = [
      { ar: 'ـ', en: 'red', meaningKey: 'red', wordType: 'adjective' },
      { ar: 'ـ', en: 'green', meaningKey: 'green', wordType: 'adjective' },
      { ar: 'ـ', en: 'pen', meaningKey: 'pen', wordType: 'noun' },
      { ar: 'ـ', en: 'book', meaningKey: 'book', wordType: 'noun' },
      { ar: 'ـ', en: 'wrote', meaningKey: 'wrote', wordType: 'verb' },
    ]
    const distractors = pickDistractors(thin, thin[0], 3, makeRandom(7))
    expect(distractors.map((d) => d.en)).toEqual(['green'])
  })

  // Two entries meaning the same thing must not both be offered, and the thin
  // path must not quietly stop enforcing that.
  it('still refuses a synonym even when that leaves nothing to offer', () => {
    const synonyms = [
      { ar: 'ـ', en: 'red', meaningKey: 'red', wordType: 'adjective' },
      { ar: 'ـ', en: 'crimson', meaningKey: 'red', wordType: 'adjective' },
    ]
    expect(pickDistractors(synonyms, synonyms[0], 3, makeRandom(7))).toEqual([])
  })
})

describe('choosing which word to ask', () => {
  // A group of nouns with one adjective dropped in it, book:deeds is exactly
  // this, and طَيِّبَة is the adjective. Asking it would put one option on
  // screen, because a wrong option has to be the same type of word.
  const lonely = [
    { ar: 'ـ', en: 'wholesome', meaningKey: 'wholesome', wordType: 'adjective', groups: ['deeds'] },
    { ar: 'ـ', en: 'deed', meaningKey: 'deed', wordType: 'noun', groups: ['deeds'] },
    { ar: 'ـ', en: 'reward', meaningKey: 'reward', wordType: 'noun', groups: ['deeds'] },
    { ar: 'ـ', en: 'sin', meaningKey: 'sin', wordType: 'noun', groups: ['deeds'] },
    { ar: 'ـ', en: 'truth', meaningKey: 'truth', wordType: 'noun', groups: ['deeds'] },
  ]

  it('passes over a word its cut cannot ask fairly', () => {
    for (let seed = 1; seed <= 40; seed++) {
      const q = buildQuestion(lonely, { random: makeRandom(seed) })
      expect(q.options, `seed ${seed}`).toHaveLength(4)
      expect(q.answerId, `seed ${seed}`).not.toBe('wholesome')
    }
  })

  it('still asks a shorter question when every word in the cut is thin', () => {
    const twoTypes = [
      { ar: 'ـ', en: 'red', meaningKey: 'red', wordType: 'adjective' },
      { ar: 'ـ', en: 'green', meaningKey: 'green', wordType: 'adjective' },
      { ar: 'ـ', en: 'pen', meaningKey: 'pen', wordType: 'noun' },
    ]
    const q = buildQuestion(twoTypes, { random: makeRandom(3) })
    expect(q.options.length).toBeGreaterThanOrEqual(2)
    expect(q.options.length).toBeLessThan(4)
  })

  it('says so rather than asking nothing when the bank is empty', () => {
    expect(() => buildQuestion([], { random: makeRandom(1) })).toThrow(/empty/i)
  })
})

describe('working through the bank', () => {
  it('skips words already asked this round', () => {
    const exclude = new Set(BANK.slice(0, BANK.length - 1).map((w) => w.meaningKey))
    const q = buildQuestion(BANK, { exclude, random: makeRandom(2) })
    expect(q.answerId).toBe(BANK[BANK.length - 1].meaningKey)
  })

  it('starts again once every word has been asked', () => {
    const exclude = new Set(BANK.map((w) => w.meaningKey))
    const q = buildQuestion(BANK, { exclude, random: makeRandom(2) })
    expect(q.answerId).toBeTruthy()
    expect(q.options).toHaveLength(4)
  })

  it('rejects a direction it does not know', () => {
    expect(() => buildQuestion(BANK, { direction: 'ar-fr' })).toThrow(/direction/i)
  })
})

describe('the mistakes round', () => {
  // Its answers are the handful got wrong, but its wrong options come from
  // everywhere. Fused, as every other round has them, a learner with two
  // mistakes of two different types could never be asked a full question,
  // which is exactly the day review is worth the most.
  const oneMistake = [BANK.find((word) => word.wordType === 'noun')]

  it('asks a full question from a single word got wrong', () => {
    const question = buildQuestion(oneMistake, {
      random: makeRandom(1),
      distractorBank: BANK,
    })
    expect(question.options).toHaveLength(4)
    expect(question.answerId).toBe(oneMistake[0].meaningKey)
  })

  it('still refuses to put two options of different types together', () => {
    for (let seed = 1; seed <= 50; seed += 1) {
      const question = buildQuestion(oneMistake, {
        random: makeRandom(seed),
        distractorBank: BANK,
      })
      const shown = question.options.map(
        (option) => BANK.find((word) => word.meaningKey === option.id),
      )
      expect(new Set(shown.map((word) => word.wordType)).size).toBe(1)
    }
  })

  it('still never offers two options that mean the same thing', () => {
    const question = buildQuestion(oneMistake, { random: makeRandom(7), distractorBank: BANK })
    const meanings = question.options.map((option) => option.id)
    expect(new Set(meanings).size).toBe(meanings.length)
  })

  it('asks the same questions as before when no separate option bank is given', () => {
    const withNull = buildQuestion(BANK, { random: makeRandom(3), distractorBank: null })
    const without = buildQuestion(BANK, { random: makeRandom(3) })
    expect(withNull).toEqual(without)
  })
})

describe('a meaning language the words do not have', () => {
  // The everyday set has no Urdu and there is no free human source for one, so
  // this is the shipped state, not a contrived case.
  it('says so instead of putting blank options on the screen', () => {
    expect(() => buildQuestion(BANK, { direction: 'ar-ur', random: makeRandom(1) }))
      .toThrow(/written in ur/i)
  })

  it('asks only the words that do have it, when some of the bank does', () => {
    const mixed = [
      ...BANK.slice(0, 30),
      ...URDU_BANK.slice(30, 40),
    ]
    for (let seed = 1; seed <= 30; seed += 1) {
      const q = buildQuestion(mixed, { direction: 'ar-ur', random: makeRandom(seed) })
      for (const option of q.options) expect(option.text, `seed ${seed}`).toBeTruthy()
    }
  })

  it('never offers a word with no Urdu as a wrong option', () => {
    const answer = URDU_BANK.find((w) => w.wordType === 'noun')
    const withGaps = [answer, ...BANK.filter((w) => w.wordType === 'noun').slice(0, 20)]
    expect(pickDistractors(withGaps, answer, 3, makeRandom(5), 'ur')).toEqual([])
  })
})

describe('how a wrong option is made hard to dismiss', () => {
  // English opens a gloss with its grammar, Urdu closes with it. The rule is the
  // same either way, the end it reads is not, and reading the wrong end makes
  // every option easy without anything looking broken.
  const noun = (key, en, ur) => ({ ar: 'ـ', en, ur, meaningKey: key, wordType: 'noun' })

  it('prefers the option that opens the same way, in English', () => {
    const bank = [
      noun('a', 'to carry out'),
      noun('b', 'to guide'),
      noun('c', 'He walks'),
      noun('d', 'He sleeps'),
    ]
    const chosen = pickDistractors(bank, bank[0], 1, makeRandom(3), 'en')
    expect(chosen[0].en).toBe('to guide')
  })

  it('prefers the option that closes the same way, in Urdu', () => {
    const bank = [
      noun('a', 'x', 'اللہ کے'),
      noun('b', 'x2', 'رسول کے'),
      noun('c', 'x3', 'جو رب ہے'),
      noun('d', 'x4', 'جو مالک ہے'),
    ]
    const chosen = pickDistractors(bank, bank[0], 1, makeRandom(3), 'ur')
    expect(chosen[0].ur).toBe('رسول کے')
  })

  it('reads the closing word for the answer too, not just the options', () => {
    const bank = [
      noun('a', 'x', 'جو رب ہے'),
      noun('b', 'x2', 'جو مالک ہے'),
      noun('c', 'x3', 'اللہ کے'),
      noun('d', 'x4', 'رسول کے'),
    ]
    const chosen = pickDistractors(bank, bank[0], 1, makeRandom(3), 'ur')
    expect(chosen[0].ur).toBe('جو مالک ہے')
  })
})

describe('what a word means to someone who reads Urdu', () => {
  // Only ever set on a word a person has checked, so nearly every word has
  // none, and the question has to carry both states without caring which.
  const trap = {
    ar: 'مَكَان', en: 'place', ur: 'جگہ', meaningKey: 'place', wordType: 'noun',
    urdu: { kind: 'false-friend', sense: 'گھر' },
  }

  it('rides through to the question, so the panel can warn before the answer', () => {
    const bank = [trap, ...URDU_BANK.filter((w) => w.wordType === 'noun').slice(0, 8)]
    const q = buildQuestion(bank, { direction: 'ar-ur', exclude: new Set(), random: makeRandom(1) })
    const asked = bank.find((w) => w.meaningKey === q.answerId)
    expect(q.urdu).toEqual(asked.urdu ?? null)
  })

  it('is null on a word nobody has checked, rather than missing', () => {
    const q = buildQuestion(URDU_BANK, { direction: 'ar-ur', random: makeRandom(4) })
    expect(q.urdu).toBeNull()
  })
})
