/**
 * The Basics skills, as data: each skill's markers (the additions it teaches), their rules, and the nouns and verbs
 * each skill draws. The path that weaves them, and the cards: lib/grow/basicsSkills.js.
 */
import { PATTERNS, patternAsks } from './verbPatterns'
import { ADDRESSED, PERSONS } from './wordForms'

const EVERYONE = PERSONS.map((person) => person.id)
// Taught whole; asked on a word with no ة, the ة half is left off (ruleFor).
export const TA_CLAUSE = ', and a final ة is written ت before it.'
const MINE_TAIL = `A word with an ending never takes ال as well${TA_CLAUSE}`
// What a misspelt form (wordForms.js `wrong:<kind>:*`) got wrong.
export const MISSPELT = {
  al: 'A word with an ending never takes ال as well.',
  ta: 'A final ة is written ت before an ending.',
  'sa-past': 'سَ goes only on the present, never on the past.',
  'sa-apart': 'سَ is one letter, so it is joined to the verb, never written apart.',
  'sawfa-past': 'سَوْفَ goes only before the present, never before the past.',
  'lam-past': 'لَمْ goes before the present, never the past: for the past it is مَا.',
  'lan-past': 'لَنْ goes before the present, never the past.',
  apart: 'A one-letter word is joined to the word after it, never written apart.',
  alif: 'After لِـ the ا of ال is dropped: لِلْـ.',
  gender: 'هٰذَا and ذٰلِكَ go with a masculine word; هٰذِهِ and تِلْكَ with a feminine one, as most with ة are.',
  ya: 'On a verb “me” is ـنِي; ـِي is “my”, on a noun.',
  agree: 'The word after هُوَ is a man’s, after هِيَ a woman’s (with ة), after هُمْ the plural: it agrees.',
  first: 'The first word never takes ال: the ال of the second makes both “the”.',
  tanween: 'The first word never ends in -un (ـٌ): the second word finishes it.',
}

const own = (id, end, said, pool, to = '') => ({
  id, key: `mine:${id}`, base: 'bare', persons: [null], pool: [...pool.map((one) => `mine:${one}`), `wrong:al:${id}`, `wrong:ta:${id}`],
  rule: `${end} on the end means “${said}”${to}. ${MINE_TAIL}`,
})
const fixed = (tense, person, base, rule, pool) => ({ id: person, key: `${tense}:${person}`, base, persons: [person], rule, pool })
const particle = (id, persons, base, rule, pool, toEnglish) => ({ id, key: `${id}:{p}`, base, persons, rule, pool, ...(toEnglish && { toEnglish }) })
// A noun skill's marker: no person, the form it is set beside, the forms it is told apart from.
const noun = (id, base, rule, pool) => ({ id, key: id, base, persons: [null], rule, pool })

export const SKILLS = {
  mine: {
    title: 'My, his, her',
    table: 'nouns',
    markers: [
      { ...own('my', 'ـِي', 'my', ['his', 'our', 'your']), rule: `ـِي on the end means “my”. English puts “my” before the word; Arabic adds it to the end. ${MINE_TAIL}` },
      own('his', 'ـهُ', 'his', ['my', 'her', 'their']),
      own('her', 'ـهَا', 'her', ['his', 'my', 'our']),
      own('our', 'ـنَا', 'our', ['my', 'her', 'their']),
      own('their', 'ـهُمْ', 'their', ['his', 'her', 'our']),
      own('your', 'ـكَ', 'your', ['my', 'his', 'your-all'], ', said to one man'),
      own('your-all', 'ـكُمْ', 'your', ['your', 'their', 'our'], ', said to a group'),
    ],
  },
  people: {
    title: 'One and many',
    table: 'people',
    markers: [
      noun('woman', 'man', 'ة on the end makes a word for a man a word for a woman: مُسْلِمَة a Muslim woman. English mostly uses one word for both.',
        ['man', 'men', 'women']),
      noun('men', 'man', 'ـُونَ on the end = more than two men, or men and women together. You will also see it as ـِينَ (مُسْلِمِينَ): the same plural, in another place in the sentence.',
        ['man', 'woman', 'women']),
      noun('women', 'woman', 'ـَات on the end = more than two women: the ة goes, and ـَات takes its place. English adds -s for both.',
        ['woman', 'men', 'man']),
    ],
  },
  joined: {
    title: 'And, with, for, like',
    table: 'joined',
    markers: [
      noun('and', 'the', 'وَ = and. It is one letter, so it is joined to the word after it: وَالْكِتَاب and the book.',
        ['the', 'with', 'like', 'wrong:apart:and']),
      noun('with', 'the', 'بِـ = with (or by, or in), joined to the front of the word. English writes “with” as a word of its own.',
        ['and', 'for', 'like', 'wrong:apart:with']),
      noun('for', 'the', 'لِـ = for (or to), joined to the front. Before ال the ا is dropped, so لِ and الْكِتَاب make لِلْكِتَاب.',
        ['with', 'like', 'wrong:alif:for', 'wrong:apart:for']),
      noun('like', 'the', 'كَـ = like, joined to the front: كَالْقَمَر like the moon.',
        ['and', 'with', 'for', 'wrong:apart:like']),
    ],
  },
  this: {
    title: 'This, that',
    table: 'pointing',
    markers: [
      noun('this-is', null, 'هٰذَا before a word without ال = “this is a …”: هٰذَا كِتَاب this is a book. Arabic needs no word for “is”. For a feminine word, most with ة, it is هٰذِهِ.',
        ['this', 'that-is', 'wrong:gender:this-is']),
      noun('this', 'this-is', 'With ال, هٰذَا (or هٰذِهِ) is only “this”: هٰذَا الْكِتَاب this book. So ال tells you: a whole sentence, or one thing named.',
        ['this-is', 'that', 'wrong:gender:this']),
      noun('that-is', 'this-is', 'ذٰلِكَ = that, said the same way: ذٰلِكَ قَلَم that is a pen. For a feminine word it is تِلْكَ.',
        ['that', 'this-is', 'wrong:gender:that-is']),
      noun('that', 'that-is', 'With ال, ذٰلِكَ (or تِلْكَ) is only “that”: ذٰلِكَ الْقَلَم that pen.',
        ['that-is', 'this', 'wrong:gender:that']),
    ],
  },
  pronouns: {
    title: 'He, she, I',
    table: 'pronouns',
    markers: [
      noun('he', null, 'هُوَ = he. Arabic needs no word for “is”: هُوَ مُسْلِم he is a Muslim.', ['she', 'they', 'wrong:agree:he']),
      noun('she', 'he', 'هِيَ = she, and the word after it is a woman’s, with ة: هِيَ مُسْلِمَة she is a Muslim.', ['he', 'I-woman', 'wrong:agree:she']),
      noun('they', 'he', 'هُمْ = they (men, or men and women), and the word after it takes ـُونَ: هُمْ مُسْلِمُونَ they are Muslims.',
        ['we', 'he', 'wrong:agree:they']),
      noun('I', 'he', 'أَنَا = I: a man says أَنَا مُسْلِم, a woman أَنَا مُسْلِمَة.', ['I-woman', 'he', 'we']),
      noun('we', 'they', 'نَحْنُ = we: نَحْنُ مُسْلِمُونَ we are Muslims.', ['they', 'I', 'you-all']),
      noun('you', 'he', 'أَنْتَ = you, said to one man.', ['you-woman', 'you-all', 'he']),
      noun('you-woman', 'you', 'أَنْتِ = you, said to one woman: one mark from أَنْتَ, and the word after it takes ة.', ['you', 'she', 'I-woman']),
      noun('you-all', 'they', 'أَنْتُمْ = you, said to a group: أَنْتُمْ مُسْلِمُونَ.', ['you', 'they', 'we']),
    ],
  },
  of: {
    title: 'The … of …',
    table: 'pairs',
    markers: [
      noun('of', 'the', 'Two nouns side by side say “the … of …”: كِتَاب الْمُعَلِّم the teacher’s book. The first never takes ال: the ال of the second makes both “the”. So كِتَابُ اللهِ is the Book of Allah.',
        ['the', 'turned', 'wrong:first:of', 'wrong:tanween:of']),
      noun('a', 'of', 'With no ال on the second word either, both are “a”: كِتَاب مُعَلِّم a teacher’s book.', ['of', 'turned', 'is']),
    ],
  },
  two: {
    title: 'Two',
    table: 'dual',
    markers: [
      noun('two', 'one', 'ـَانِ on the end = two: كِتَابَانِ two books. English adds a number; Arabic adds an ending, and a final ة is written ت before it. You will also see ـَيْنِ (كِتَابَيْنِ): the same two, in another place in the sentence.',
        ['one', 'the-two', 'wrong:ta:two']),
      noun('the-two', 'the', 'With ال in front, الْكِتَابَانِ = the two books.', ['the', 'two', 'one']),
    ],
  },
  past: {
    title: 'The past',
    table: 'verbs',
    markers: [
      fixed('past', 'he', null, 'The past for “he” is the verb as it is: كَتَبَ he wrote. English adds -ed (or changes the word); Arabic adds an ending for who did it.', ['past:they', 'past:I', 'past:we', 'present:he']),
      fixed('past', 'they', 'past:he', 'ـُوا on the end = they did it. The ا is written, not said.', ['past:he', 'past:we', 'past:I', 'present:they']),
      fixed('past', 'I', 'past:he', 'ـْتُ on the end = I did it.', ['past:he', 'past:they', 'past:we', 'present:I']),
      fixed('past', 'we', 'past:he', 'ـْنَا on the end = we did it.', ['past:he', 'past:they', 'past:I', 'present:we']),
      fixed('past', 'you', 'past:he', 'ـْتَ on the end = you did it, said to one man.', ['past:he', 'past:we', 'past:they', 'past:you-all', 'present:you']),
      fixed('past', 'you-all', 'past:you', 'ـْتُمْ on the end = you all did it.', ['past:you', 'past:they', 'past:we', 'present:you-all']),
      fixed('past', 'she', 'past:he', 'ـَتْ on the end = she did it. Watch the marks: ـَتْ she, ـْتَ you, ـْتُ I.', ['past:he', 'past:you', 'past:I', 'present:she']),
    ],
  },
  present: {
    title: 'The present',
    table: 'verbs',
    markers: [
      fixed('present', 'he', 'past:he', 'The present adds a letter in front: يَـ = he. English adds -s: he writes.', ['present:they', 'present:I', 'present:we', 'past:he']),
      fixed('present', 'she', 'present:he', 'تَـ in front = she.', ['present:he', 'present:I', 'present:we', 'past:she']),
      fixed('present', 'they', 'present:he', 'يَـ in front and ـُونَ on the end = they.', ['present:he', 'present:we', 'present:you-all', 'past:they']),
      fixed('present', 'I', 'present:he', 'أَ in front = I.', ['present:he', 'present:we', 'present:she', 'past:I']),
      fixed('present', 'we', 'present:I', 'نَ in front = we.', ['present:I', 'present:he', 'present:they', 'past:we']),
      fixed('present', 'you', 'present:he', 'تَـ in front = you, said to one man: the same as “she”, and the sentence tells you which.', ['present:he', 'present:I', 'present:you-all', 'past:you']),
      fixed('present', 'you-all', 'present:they', 'تَـ in front and ـُونَ on the end = you all.', ['present:they', 'present:you', 'present:we', 'past:you-all']),
    ],
  },
  negation: {
    title: 'Not',
    table: 'verbs',
    markers: [
      // لَا + present can mean “won’t” too (لَا يُؤْمِنُونَ, they will not believe), so it is never set beside لَنْ.
      particle('not', EVERYONE, 'present:{p}', 'لَا before the present = not: “doesn’t” or “don’t” (in the Qur’an often “won’t”). English adds a word in front too.', ['present:{p}', 'not-past:{p}']),
      particle('not-past', EVERYONE, 'present:{p}', 'لَمْ before the present = didn’t. The last ـُ becomes ـْ, and ـُونَ becomes ـُوا.', ['not:{p}', 'not-future:{p}', 'past:{p}', 'wrong:lam-past:{p}']),
      particle('not-future', EVERYONE, 'future:{p}', 'لَنْ before the present = won’t. The last ـُ becomes ـَ, and ـُونَ becomes ـُوا.', ['future:{p}', 'not-past:{p}', 'wrong:lan-past:{p}']),
      particle('not-past-ma', EVERYONE, 'past:{p}', 'مَا before the past can say didn’t too, like لَمْ before the present. (مَا has other jobs as well, such as “what”.)', ['not:{p}', 'not-future:{p}', 'past:{p}']),
    ],
  },
  command: {
    title: 'Do! Don’t!',
    table: 'verbs',
    markers: [
      particle('command', ADDRESSED, 'present:{p}', 'A command is the present without its front letter: it ends in ـْ (to a group, ـُوا) and starts with ا, said اُ when the present has ـُ in the middle (اُكْتُبْ), else اِ (اِجْلِسْ). English drops “you” the same way.', ['present:{p}', 'past:{p}', 'prohibit:{p}']),
      particle('prohibit', ADDRESSED, 'command:{p}', 'لَا before the “you” present, ending in ـْ (to a group, ـُوا) = “Don’t …!”', ['command:{p}', 'present:{p}', 'past:{p}', 'future:{p}']),
    ],
  },
  future: {
    title: 'Will',
    table: 'verbs',
    markers: [
      // The bare present can mean "will" too (يَكْتُبُ, he will write), so it is no wrong answer to "he will write";
      // shown سَيَكْتُبُ, though, "he writes" is a wrong meaning, so it stays in the English direction.
      particle('future', EVERYONE, 'present:{p}', 'سَ joined to the front of the present = will. English adds a word; Arabic adds one letter.',
        ['past:{p}', 'not-future:{p}', 'wrong:sa-past:{p}', 'wrong:sa-apart:{p}'], ['present:{p}', 'past:{p}', 'not-future:{p}']),
      particle('future-sawfa', EVERYONE, 'future:{p}', 'سَوْفَ, a word of its own before the present, = will too.',
        ['past:{p}', 'not-future:{p}', 'wrong:sawfa-past:{p}'], ['present:{p}', 'past:{p}', 'not-future:{p}']),
    ],
  },
  object: {
    title: 'Him, her, me',
    table: 'objects',
    markers: [
      noun('him', 'he', 'ـهُ on the end of a verb = him (or it): سَمِعَهُ he heard him. English puts “him” after the verb as a word; Arabic joins it on.',
        ['her', 'them', 'me']),
      noun('her', 'he', 'ـهَا on the end of a verb = her (or it): سَمِعَهَا he heard her.', ['him', 'them', 'us']),
      noun('them', 'he', 'ـهُمْ on the end of a verb = them.', ['him', 'her', 'you-all']),
      noun('me', 'he', 'ـنِي on the end of a verb = me: سَمِعَنِي he heard me. Not ـِي, which is “my” on a noun.', ['us', 'him', 'wrong:ya:me']),
      noun('us', 'he', 'ـنَا on the end of a verb = us. Watch the mark before it: سَمِعَنَا he heard us, but سَمِعْنَا we heard.',
        ['me', 'them', 'we']),
      noun('you', 'he', 'ـكَ on the end of a verb = you, said to one man.', ['you-all', 'him', 'me']),
      noun('you-all', 'he', 'ـكُمْ on the end of a verb = you, said to a group.', ['you', 'them', 'us']),
    ],
  },
  patterns: {
    title: 'Verb patterns',
    table: 'families',
    has: (family, marker) => Boolean(family.forms[marker.key]),
    asks: patternAsks,
    markers: [
      ['II', 'The middle letter doubled often means making someone do it, or doing it a lot: عَلِمَ he knew, عَلَّمَ he taught (made him know).'],
      ['III', 'An ا after the first letter often means doing it with or to someone: كَتَبَ he wrote, كَاتَبَ he wrote to someone.'],
      ['IV', 'أَ in front, and no vowel on the first letter, often means making someone do it: سَمِعَ he heard, أَسْمَعَ he made someone hear.'],
      ['V', 'تَ in front of form II turns it back on the doer: عَلَّمَ he taught, تَعَلَّمَ he learnt (taught himself).'],
      ['VI', 'تَ in front of form III often means doing it to each other, so it is mostly said of “they”: تَكَاتَبُوا they wrote to each other.'],
      ['VII', 'اِنْ in front often means it got done, by itself, with no doer named: فَتَحَ he opened, اِنْفَتَحَ it came open.'],
      ['VIII', 'A ت after the first letter often means doing it for yourself, or with effort: سَمِعَ he heard, اِسْتَمَعَ he listened.'],
      ['X', 'اِسْتَ in front often means asking for it: عَلِمَ he knew, اِسْتَعْلَمَ he asked to know.'],
    ].map(([form, rule]) => noun(form, 'I', `${PATTERNS[form].shape}: ${rule} Often, not always: each verb’s meaning is still learnt.`, [])),
  },
}

/** Whose a thing is (“the teacher’s book”): people who own, and things owned; every thing goes with every owner. */
export const OWNERS = ['teacher', 'student', 'man', 'boy', 'girl', 'doctor', 'friend', 'driver', 'merchant', 'neighbour', 'guest', 'child']
export const THINGS = ['book', 'pen', 'car', 'house', 'bag', 'phone', 'key', 'cup', 'ball', 'notebook', 'picture', 'ticket', 'room', 'door']

/** Things whose English for many is the word with -s: book, books (not box, city). */
export const DUAL = [
  'book', 'pen', 'key', 'car', 'phone', 'bag', 'cup', 'ball', 'notebook', 'ticket', 'picture', 'room', 'door', 'house',
  'school', 'garden', 'mosque', 'street', 'ship', 'tree', 'window', 'table', 'bed',
]

/** The verbs “him, her, me” is asked on: each is done to a person, and its English past takes one after it. */
export const OBJECT_VERBS = ['hear', 'remember', 'carry', 'understand', 'wash']

/**
 * The nouns the possessive skill draws: things a person has, every one taking the endings plainly (wordForms canPossess).
 * Not the body (or a shirt): “their heart”, “our face” are said with the plural in Arabic (قُلُوبُهُمْ), which is not taught yet.
 */
export const OWNED = [
  'book', 'house', 'pen', 'car', 'school', 'notebook', 'teacher', 'room', 'bed', 'key', 'cup', 'phone', 'bag', 'friend',
  'sister', 'doctor', 'family', 'garden', 'city', 'village', 'picture',
  'ball', 'horse', 'cat', 'dog', 'camel', 'lesson', 'question', 'word', 'language', 'door', 'table', 'shop', 'ticket', 'neighbour',
]

/** Things “with the …”, “for the …” and “like the …” all fit; none starts with ل, which لِـ would spell otherwise (لِلَّيْل). */
export const JOINED = ['book', 'pen', 'key', 'car', 'phone', 'bag', 'cup', 'spoon', 'knife', 'ball', 'notebook', 'ticket', 'box', 'candle', 'picture', 'bottle']

/** Things whose gender the ة shows: masculine without it, feminine with it (not شَمْس or يَد, feminine with none). */
export const POINTED = [
  'book', 'car', 'pen', 'school', 'house', 'room', 'door', 'key', 'bag', 'phone', 'notebook', 'cup', 'city', 'garden',
  'picture', 'ball', 'tree', 'mosque', 'ticket', 'window', 'table', 'bed', 'street', 'ship', 'box', 'cat',
]

