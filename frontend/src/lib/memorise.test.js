import { describe, expect, it } from 'vitest'

import { recitedForm } from './arabicText'
import {
  blanksFor, CHOICES, DEFAULT_DIFFICULTY, DIFFICULTIES, fromMemory, isRight, makeRandom,
  optionsFor, pagesOf, printedPageOf, score, wordsOf,
} from './memorise'

// Al-Ikhlas, as the surah endpoint hands it over.
const IKHLAS = [
  { id: 1, arabic: 'قُلْ هُوَ ٱللَّهُ أَحَدٌ' },
  { id: 2, arabic: 'ٱللَّهُ ٱلصَّمَدُ' },
  { id: 3, arabic: 'لَمْ يَلِدْ وَلَمْ يُولَدْ' },
  { id: 4, arabic: 'وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ' },
]

describe('cutting a book into pages', () => {
  it('fills a page up to about the asked-for size and starts the next one', () => {
    const lines = Array.from({ length: 10 }, (_, i) => ({ id: i, arabic: 'ا ب ج د ه' }))
    const pages = pagesOf(lines, 12)
    // 5 words a line: two lines fit in 12, a third would make 15.
    expect(pages.map((p) => p.length)).toEqual([2, 2, 2, 2, 2])
  })

  it('never cuts a line in half, however long it is', () => {
    const long = { id: 1, arabic: Array(40).fill('كلمة').join(' ') }
    const pages = pagesOf([long, { id: 2, arabic: 'ا ب' }], 10)
    expect(pages[0]).toEqual([long])
    expect(pages[1]).toHaveLength(1)
  })

  it('loses no line and keeps them in order', () => {
    const pages = pagesOf(IKHLAS, 6)
    expect(pages.flat().map((l) => l.id)).toEqual([1, 2, 3, 4])
  })

  it('gives nothing back for nothing', () => {
    expect(pagesOf([])).toEqual([])
  })

  it('groups by the printed page when the lines know one, ignoring word count', () => {
    // Three short lines on one printed page and one long line on the next. By
    // word count these would break in the middle of page 30; by the printing
    // they do not, which is the whole point of having the layout.
    const lines = [
      { id: 1, arabic: 'ا ب', page: 30 },
      { id: 2, arabic: 'ج د', page: 30 },
      { id: 3, arabic: 'ه و ز ح ط ي ك ل', page: 30 },
      { id: 4, arabic: 'م ن', page: 31 },
    ]
    const pages = pagesOf(lines, 4)
    expect(pages.map((page) => page.map((line) => line.id))).toEqual([[1, 2, 3], [4]])
    expect(printedPageOf(pages[0])).toBe(30)
    expect(printedPageOf(pages[1])).toBe(31)
  })

  it('keeps a line with no page number on the page already open', () => {
    // A hole in the layout must not start a page of its own, or one unlisted
    // ayah would silently split a printed page in two.
    const lines = [
      { id: 1, arabic: 'ا', page: 5 },
      { id: 2, arabic: 'ب' },
      { id: 3, arabic: 'ج', page: 6 },
    ]
    expect(pagesOf(lines).map((page) => page.map((line) => line.id))).toEqual([[1, 2], [3]])
  })

  it('says a word-counted page has no printed number rather than inventing one', () => {
    expect(printedPageOf(pagesOf(IKHLAS, 6)[0])).toBe(null)
  })
})

describe('choosing which words to hide', () => {
  const page = pagesOf(IKHLAS, 100)[0]

  it('never takes the word a line starts on', () => {
    for (let seed = 1; seed <= 30; seed++) {
      const blanks = blanksFor(page, 1, makeRandom(seed))
      for (const key of blanks) expect(key.endsWith(':0'), key).toBe(false)
    }
  })

  it('leaves a word standing between two gaps below half', () => {
    for (let seed = 1; seed <= 30; seed++) {
      const blanks = blanksFor(page, 1 / 3, makeRandom(seed))
      for (const key of blanks) {
        const [l, w] = key.split(':').map(Number)
        expect(blanks.has(`${l}:${w + 1}`), `${key} seed ${seed}`).toBe(false)
      }
    }
  })

  it('hides about the share it was asked for', () => {
    const words = page.reduce((n, l) => n + wordsOf(l.arabic).length, 0)
    const blanks = blanksFor(page, 1 / 3, makeRandom(4))
    // Every line keeps its first word, so a third of a four-word line is one.
    expect(blanks.size).toBeGreaterThan(0)
    expect(blanks.size).toBeLessThanOrEqual(Math.ceil(words / 3))
  })

  it('hides nothing at all when nothing was asked for', () => {
    expect(blanksFor(page, 0, makeRandom(1)).size).toBe(0)
  })

  it('gives the same gaps for the same seed and different ones for another', () => {
    const a = [...blanksFor(page, 1 / 3, makeRandom(7))].sort()
    const b = [...blanksFor(page, 1 / 3, makeRandom(7))].sort()
    expect(a).toEqual(b)
    const c = [...blanksFor(page, 1 / 3, makeRandom(99))].sort()
    expect(a.join()).not.toBe(c.join())
  })
})

describe('judging what was typed', () => {
  it('accepts the word without any of the marks a keyboard has no key for', () => {
    expect(isRight('الله', 'ٱللَّهُ')).toBe(true)      // wasla alif and vowels
    expect(isRight('احد', 'أَحَدٌ')).toBe(true)         // hamza on the alif
    expect(isRight('علي', 'عَلَىٰ')).toBe(true)         // alif maqsura
    expect(isRight('  يلد  ', 'يَلِدْ')).toBe(true)     // stray spaces
  })

  it('accepts a standing fatha spelt as an alif and spelt without one', () => {
    // The mark is a long a. Later spelling writes it as a whole letter in some
    // words and not in others, and nothing in the text says which; so a reader
    // typing either is right. ٱلصَّٰلِحَٰتِ was marked wrong before this.
    expect(isRight('الصالحات', 'ٱلصَّٰلِحَٰتِ')).toBe(true)
    expect(isRight('الصلحت', 'ٱلصَّٰلِحَٰتِ')).toBe(true)
    expect(isRight('ذلك', 'ذَٰلِكَ')).toBe(true)
    expect(isRight('ذالك', 'ذَٰلِكَ')).toBe(true)
    expect(isRight('الرحمن', 'ٱلرَّحْمَٰنِ')).toBe(true)
    // Still a different word, however the mark is read.
    expect(isRight('كتاب', 'ٱلصَّٰلِحَٰتِ')).toBe(false)
  })

  it('reads a standing fatha on an already-long letter as adding nothing', () => {
    expect(isRight('عيسى', 'عِيسَىٰ')).toBe(true)
    expect(isRight('على', 'عَلَىٰ')).toBe(true)
  })

  it('still refuses a different word', () => {
    expect(isRight('احد', 'ٱلصَّمَدُ')).toBe(false)
    expect(isRight('', 'أَحَدٌ')).toBe(false)
    // ة and ه are two letters, not one written two ways.
    expect(isRight('رحمه', 'رَحْمَة')).toBe(false)
  })

  it('reduces an ayah number or a recitation mark to nothing', () => {
    expect(recitedForm('۩')).toBe('')
    expect(recitedForm('٣')).toBe('')
  })
})

describe('offering four words instead of a box to type in', () => {
  const POOL = wordsOf(
    'ٱلْمُتَّقِينَ ٱلْمُؤْمِنِينَ ٱلْمُفْسِدِينَ ٱلْكِتَٰبُ رَيْبَ فِيهِ هُدًى نَارٌ سَمَآءٌ',
  )
  const answer = 'ٱلْمُتَّقِينَ'

  it('always includes the right word', () => {
    for (let seed = 1; seed <= 20; seed++) {
      expect(optionsFor(answer, POOL, makeRandom(seed))).toContain(answer)
    }
  })

  it('offers as many as the config asks for, and never the same word twice', () => {
    const options = optionsFor(answer, POOL, makeRandom(5))
    expect(options).toHaveLength(CHOICES)
    expect(new Set(options.map(recitedForm)).size).toBe(CHOICES)
  })

  it('picks the words that look like the answer, not any three', () => {
    // ٱلْمُؤْمِنِينَ and ٱلْمُفْسِدِينَ open the same way and end the same way;
    // نَارٌ shares nothing. A reader dismisses نَارٌ without reading it.
    const options = optionsFor(answer, POOL, makeRandom(5)).map(recitedForm)
    expect(options).toContain(recitedForm('ٱلْمُؤْمِنِينَ'))
    expect(options).toContain(recitedForm('ٱلْمُفْسِدِينَ'))
    expect(options).not.toContain(recitedForm('نَارٌ'))
  })

  it('never offers the answer a second time under another spelling', () => {
    const twice = [...POOL, 'المتقين']
    const options = optionsFor(answer, twice, makeRandom(2)).map(recitedForm)
    expect(options.filter((o) => o === recitedForm(answer))).toHaveLength(1)
  })

  it('offers fewer rather than repeating itself when the book is small', () => {
    expect(optionsFor(answer, ['نَارٌ'], makeRandom(1))).toHaveLength(2)
    expect(optionsFor(answer, [], makeRandom(1))).toEqual([answer])
  })

  it('does not always put the answer in the same place', () => {
    const places = new Set(
      Array.from({ length: 25 }, (_, i) =>
        optionsFor(answer, POOL, makeRandom(i + 1)).indexOf(answer)),
    )
    expect(places.size).toBeGreaterThan(1)
  })
})

describe('marking a page', () => {
  const page = pagesOf(IKHLAS, 100)[0]

  it('counts only the gaps, and only the ones filled in right', () => {
    const blanks = blanksFor(page, 1, makeRandom(3))
    const answers = {}
    for (const key of blanks) {
      const [l, w] = key.split(':').map(Number)
      answers[key] = wordsOf(page[l].arabic)[w]
    }
    expect(score(page, blanks, answers)).toEqual({ right: blanks.size, total: blanks.size })

    const [first] = [...blanks]
    expect(score(page, blanks, { ...answers, [first]: 'خطأ' }).right).toBe(blanks.size - 1)
  })

  it('counts an untouched page as none right rather than throwing', () => {
    const blanks = blanksFor(page, 1 / 3, makeRandom(2))
    expect(score(page, blanks, {})).toEqual({ right: 0, total: blanks.size })
  })
})

// The panel looks a difficulty up by id and uses what comes back without
// checking, so a default that is not in the list would be a blank page rather
// than a wrong one. Nothing else notices, which is why this is here.
describe('the settings in memorise.json', () => {
  it('names a default that is one of its own difficulties', () => {
    expect(DIFFICULTIES.map((d) => d.id)).toContain(DEFAULT_DIFFICULTY)
  })

  it('gives every difficulty its own id, a label, and a share of 0 to 1', () => {
    expect(new Set(DIFFICULTIES.map((d) => d.id)).size).toBe(DIFFICULTIES.length)
    for (const d of DIFFICULTIES) {
      expect(d.label).toBeTruthy()
      expect(d.title).toBeTruthy()
      expect(d.share).toBeGreaterThanOrEqual(0)
      expect(d.share).toBeLessThanOrEqual(1)
    }
  })

  it('offers at least two words to choose between', () => {
    // One would be the answer alone, and picking would not be a question.
    expect(CHOICES).toBeGreaterThanOrEqual(2)
  })
})

describe('a page said from memory', () => {
  it('covers every word but the first', () => {
    const blanks = fromMemory(IKHLAS)
    const words = IKHLAS.reduce((n, line) => n + wordsOf(line.arabic).length, 0)
    expect(blanks.size).toBe(words - 1)
    // قُلْ is the cue, and the opening of every ayah after it is not.
    expect(blanks.has('0:0')).toBe(false)
    expect(blanks.has('1:0')).toBe(true)
    expect(blanks.has('2:0')).toBe(true)
  })

  it('starts wherever it is told to, leaving what came before it printed', () => {
    // The sixth word of the surah counting from zero, which is where its third
    // ayah begins. Any word of the page may be the one, not only a line's
    // first: the reader picks it by pressing the word itself.
    const blanks = fromMemory(IKHLAS, 6)
    // Nothing above the starting ayah is covered: nobody claimed to recite it.
    expect(blanks.has('0:0')).toBe(false)
    expect(blanks.has('1:1')).toBe(false)
    // The word to start on is shown; everything after it is not.
    expect(blanks.has('2:0')).toBe(false)
    expect(blanks.has('2:1')).toBe(true)
    expect(blanks.has('3:0')).toBe(true)
  })
})
