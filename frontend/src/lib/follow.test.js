import { describe, expect, it } from 'vitest'

import config from '../recite.json'
import { bySound, CHECK, follow, isOfPage, joinWindows, MISSED, SAID, WAITING, wordsHeard, WRONG } from './follow'

// Al-Fatihah 1:6-7, the run the prototype recites, as the page holds it.
const PAGE = [
  'ٱهْدِنَا', 'ٱلصِّرَٰطَ', 'ٱلْمُسْتَقِيمَ',
  'صِرَٰطَ', 'ٱلَّذِينَ', 'أَنْعَمْتَ', 'عَلَيْهِمْ',
  'غَيْرِ', 'ٱلْمَغْضُوبِ', 'عَلَيْهِمْ', 'وَلَا', 'ٱلضَّآلِّينَ',
]

/** What was said, spelled the plain way a microphone writes it. */
const SPOKEN = [
  'اهدنا', 'الصراط', 'المستقيم',
  'صراط', 'الذين', 'أنعمت', 'عليهم',
  'غير', 'المغضوب', 'عليهم', 'ولا', 'الضالين',
]

/** States only, which is what nearly every test is about. */
const statesOf = (page, heard, how) => follow(page, heard, { ended: true, ...how }).words.map((w) => w.state)

describe('reciting it right', () => {
  it('marks every word said and says where the reciter is', () => {
    const answer = follow(PAGE, SPOKEN, { ended: true })
    expect(answer.words.every((w) => w.state === SAID)).toBe(true)
    expect(answer.extras).toEqual([])
    expect(answer.at).toBe(PAGE.length)
  })

  it('follows the letters ear, which writes some vowels and leaves others out', () => {
    // Real output of backend/services/recitation/letters.py on a recording of 112:1.
    expect(statesOf(['قُلْ', 'هُوَ', 'ٱللَّهُ', 'أَحَدٌ'], wordsHeard('قُل هوَ اللَّهُ أَحَدٌ')))
      .toEqual([SAID, SAID, SAID, SAID])
  })

  it('does not mark a spelling as a mistake', () => {
    // The one that must never break: the Qur'an's standing alef against the
    // full alef anybody transcribing writes.
    expect(statesOf(['مَٰلِكِ', 'يَوْمِ', 'ٱلدِّينِ'], ['مالك', 'يوم', 'الدين']))
      .toEqual([SAID, SAID, SAID])
  })

  it('leaves the words not reached yet plain, and does not call them missed', () => {
    const answer = follow(PAGE, SPOKEN.slice(0, 3), { ended: true })
    expect(answer.at).toBe(3)
    expect(answer.words.slice(0, 3).every((w) => w.state === SAID)).toBe(true)
    expect(answer.words.slice(3).every((w) => w.state === WAITING)).toBe(true)
  })

  it('has nothing to say before a word is spoken', () => {
    const answer = follow(PAGE, [])
    expect(answer.at).toBe(0)
    expect(answer.words.every((w) => w.state === WAITING)).toBe(true)
  })

  it('gives nothing back for no page', () => {
    expect(follow([], ['الله'])).toEqual({ at: 0, began: null, words: [], extras: [], started: false })
  })
})

describe('sound in the room is not somebody reciting', () => {
  it('marks nothing at all until enough of the page has been heard', () => {
    // Really happened: music was playing, the engine returned موسيقى, and the
    // page showed twelve mistakes made by somebody who had not said a word.
    const noise = ['موسيقى', 'موسيقى', 'مرشاك', 'كي', 'توقي', 'كونه']
    const answer = follow(PAGE, noise, { ended: true })
    expect(answer.started).toBe(false)
    expect(answer.words.every((w) => w.state === WAITING)).toBe(true)
    expect(answer.extras).toEqual([])
    expect(answer.at).toBe(0)
  })

  it('starts marking as soon as the reciter is plainly on the page', () => {
    const answer = follow(PAGE, SPOKEN.slice(0, 2), { ended: true })
    expect(answer.started).toBe(true)
    expect(answer.words[0].state).toBe(SAID)
  })

  it('counts a near miss towards being on the page, but not a wrong word', () => {
    expect(follow(PAGE, ['اهدنا', 'السراط'], { ended: true }).started).toBe(true)
    expect(follow(PAGE, ['اهدنا', 'وما'], { ended: true }).started).toBe(false)
  })
})

describe('a word that sounds like the one on the page', () => {
  it('is orange, and shows what came back', () => {
    const heard = [...SPOKEN]
    heard[1] = 'السراط'
    const answer = follow(PAGE, heard, { ended: true })
    expect(answer.words[1].state).toBe(CHECK)
    expect(answer.words[1].heard).toBe('السراط')
    expect(answer.words.filter((w) => w.state !== SAID)).toHaveLength(1)
  })

  it('is preferred over reading it as a word lost and a word gained', () => {
    const heard = [...SPOKEN]
    heard[11] = 'الظالين'
    const answer = follow(PAGE, heard, { ended: true })
    expect(answer.words[11].state).toBe(CHECK)
    expect(answer.extras).toEqual([])
  })
})

describe('a word that is plainly the wrong word', () => {
  it('is red, and shows what came back', () => {
    const heard = [...SPOKEN]
    heard[10] = 'وما'
    const answer = follow(PAGE, heard, { ended: true })
    expect(answer.words[10]).toEqual({ word: 'وَلَا', state: WRONG, heard: 'وما' })
    expect(answer.extras).toEqual([])
  })
})

describe('a word skipped', () => {
  it('is marked on the page and the rest still lines up', () => {
    const heard = SPOKEN.filter((_, i) => i !== 8)
    const states = statesOf(PAGE, heard)
    expect(states[8]).toBe(MISSED)
    expect(states.filter((s) => s !== SAID)).toEqual([MISSED])
  })

  it('is still caught when it is the very first word', () => {
    expect(statesOf(PAGE, SPOKEN.slice(1))[0]).toBe(MISSED)
  })

  it('is not claimed for words above where reciting began', () => {
    // Somebody who opens the page at the last ayah never said the ones above.
    const states = statesOf(PAGE, SPOKEN.slice(7), { startAt: 7 })
    expect(states.slice(0, 7).every((s) => s === WAITING)).toBe(true)
    expect(states.slice(7).every((s) => s === SAID)).toBe(true)
  })
})

describe('where the reciter began, when nobody said', () => {
  // startAt null is the whole question: the reader pressed no word, they just
  // started reciting, and the words themselves have to say where from.
  const unasked = { startAt: null, ended: true }

  it('is the top of the page when they started at the top', () => {
    expect(follow(PAGE, SPOKEN, unasked).began).toBe(0)
  })

  it('is found without being told, when they began halfway down', () => {
    const answer = follow(PAGE, SPOKEN.slice(3), unasked)
    expect(answer.began).toBe(3)
    // And the three words above are not accusations. Nobody claimed them.
    expect(answer.words.slice(0, 3).every((w) => w.state === WAITING)).toBe(true)
  })

  it('is found when they began near the foot of the page', () => {
    // The case that made this worth writing: charging for the skipped words
    // above made throwing the recitation away cheaper than lining it up, so a
    // reciter starting at the last ayah was told they were reciting some other
    // page entirely.
    const answer = follow(PAGE, SPOKEN.slice(10), unasked)
    expect(answer.began).toBe(10)
    expect(answer.started).toBe(true)
  })

  it('is not known until enough of this page has been heard', () => {
    // One word is not a recitation of this page, it is a word. Guessing a
    // start from it would cover the page from a place nobody recited.
    expect(follow(PAGE, SPOKEN.slice(3, 4), { startAt: null }).began).toBe(null)
    expect(follow([], SPOKEN, unasked).began).toBe(null)
  })

  it('says nothing while the pairing is too new to have settled', () => {
    // Still reciting, and only two words in. settle-words has not passed them.
    expect(follow(PAGE, SPOKEN.slice(0, 2), { startAt: null }).began).toBe(null)
  })

  it('picks the right one of two identical words on the same page', () => {
    // عليهم is printed twice, at 6 and at 9, and the recitation starts on one
    // of them. Reading it as the earlier would mean the two words after it
    // were skipped, and skipping costs; starting at the later leaves only
    // words above it, which cost nothing because nobody claimed them. So the
    // cheapest reading is the true one, without a rule being written for it.
    expect(follow(PAGE, SPOKEN.slice(9), unasked).began).toBe(9)
  })
})

describe('a word added that is not in the book', () => {
  it('is reported with the word it came after', () => {
    const heard = [...SPOKEN.slice(0, 3), 'يا', 'رب', ...SPOKEN.slice(3)]
    const answer = follow(PAGE, heard, { ended: true })
    expect(answer.words.every((w) => w.state === SAID)).toBe(true)
    expect(answer.extras).toEqual([
      { after: 2, heard: 'يا' },
      { after: 2, heard: 'رب' },
    ])
  })

  it('is not what a repeated word is', () => {
    // Steadying yourself by going back over the last words is not a mistake.
    const heard = [...SPOKEN.slice(0, 3), 'الصراط', 'المستقيم', ...SPOKEN.slice(3)]
    const answer = follow(PAGE, heard, { ended: true })
    expect(answer.extras).toEqual([])
    expect(answer.words.every((w) => w.state === SAID)).toBe(true)
  })
})

describe('nothing is marked the moment it is said', () => {
  const settle = config['settle-words']

  it('holds a mistake plain until enough words have gone past it', () => {
    const heard = [...SPOKEN]
    heard[0] = 'وما'
    // The mistake and only one word after it: too early to say so.
    expect(follow(PAGE, heard.slice(0, 2)).words[0].state).toBe(WAITING)
    expect(follow(PAGE, heard.slice(0, 2 + settle)).words[0].state).toBe(WRONG)
  })

  it('shows a word being right straight away, because nobody is accused by it', () => {
    // Straight away means as soon as the reciter is known to be on this page,
    // which takes anchor-words words. One word alone could be the room.
    expect(follow(PAGE, SPOKEN.slice(0, 1)).words[0].state).toBe(WAITING)
    expect(follow(PAGE, SPOKEN.slice(0, 2)).words[0].state).toBe(SAID)
    expect(follow(PAGE, SPOKEN.slice(0, 2)).words[1].state).toBe(SAID)
  })

  it('settles everything when the reciter stops', () => {
    const heard = [...SPOKEN]
    heard[11] = 'وما'
    expect(follow(PAGE, heard).words[11].state).toBe(WAITING)
    expect(follow(PAGE, heard, { ended: true }).words[11].state).toBe(WRONG)
  })

  it('holds an added word back for the same few words', () => {
    const heard = [...SPOKEN.slice(0, 3), 'يا', ...SPOKEN.slice(3)]
    expect(follow(PAGE, heard.slice(0, 5)).extras).toEqual([])
    expect(follow(PAGE, heard.slice(0, 5 + settle)).extras).toEqual([{ after: 2, heard: 'يا' }])
  })

  it('reads a stray last word as the next word said wrongly, until more is said', () => {
    // Nothing separates "you added a word" from "you said the next word wrong"
    // while that word is the last thing heard. The gentler of the two is
    // chosen, the same way orange is chosen over red, and it is put right by
    // itself the moment the reciter carries on.
    const stray = [...SPOKEN.slice(0, 3), 'يا']
    expect(follow(PAGE, stray, { ended: true }).words[3].state).toBe(WRONG)
    expect(follow(PAGE, stray, { ended: true }).extras).toEqual([])

    const carriedOn = [...stray, ...SPOKEN.slice(3)]
    const answer = follow(PAGE, carriedOn, { ended: true })
    expect(answer.words[3].state).toBe(SAID)
    expect(answer.extras).toEqual([{ after: 2, heard: 'يا' }])
  })
})

describe('a transcript that changes its mind', () => {
  it('answers only from what it is given now, never from what it was given before', () => {
    const wrong = [...SPOKEN]
    wrong[4] = 'اللذان'
    const first = follow(PAGE, wrong, { ended: true })
    expect(first.words[4].state).toBe(WRONG)

    // The next window comes back with the word heard properly. Nothing is
    // carried over, so the mark goes.
    const second = follow(PAGE, SPOKEN, { ended: true })
    expect(second.words[4].state).toBe(SAID)
    expect(second).toEqual(follow(PAGE, SPOKEN, { ended: true }))
  })
})

describe('reading a window of sound as words', () => {
  it('drops the full stop the engine wrote, which is not part of the word', () => {
    // Really came back: "ولا الضال." against وَلَا ٱلضَّآلِّينَ.
    expect(wordsHeard('إياك نعبد وإياك نستعين.'))
      .toEqual(['إياك', 'نعبد', 'وإياك', 'نستعين'])
  })

  it('keeps a word said with a stop on it as the same word', () => {
    expect(follow(['مَٰلِكِ', 'يَوْمِ', 'ٱلدِّينِ'], wordsHeard('مالك يوم الدين.'), { ended: true })
      .words.every((w) => w.state === SAID)).toBe(true)
  })

  it('leaves out ayah numbers and anything else not Arabic', () => {
    expect(wordsHeard('الحمد لله 2 (rab) العالمين'))
      .toEqual(['الحمد', 'لله', 'العالمين'])
  })

  it('gives nothing back for nothing said', () => {
    expect(wordsHeard('')).toEqual([])
    expect(wordsHeard(undefined)).toEqual([])
  })

  it('knows a reading with nothing of the page in it', () => {
    // The room, after the reciter has finished. Letting it through put موسيقى
    // on the page as a word said.
    expect(isOfPage(['موسيقى'], PAGE)).toBe(false)
    expect(isOfPage([], PAGE)).toBe(false)
    expect(isOfPage(['موسيقى', 'الصراط'], PAGE)).toBe(true)
    expect(isOfPage(['المستقيم'], PAGE)).toBe(true)
  })
})

describe('joining one window of sound to the next', () => {
  it('says the words in the overlap once', () => {
    expect(joinWindows(['الحمد', 'لله', 'رب'], ['لله', 'رب', 'العالمين']))
      .toEqual(['الحمد', 'لله', 'رب', 'العالمين'])
  })

  it('keeps the longest overlap, not the first word that happens to match', () => {
    expect(joinWindows(['عليهم', 'غير', 'عليهم', 'ولا'], ['عليهم', 'ولا', 'الضالين']))
      .toEqual(['عليهم', 'غير', 'عليهم', 'ولا', 'الضالين'])
  })

  it('keeps both when the reciter has moved on and nothing overlaps', () => {
    expect(joinWindows(['الحمد', 'لله'], ['مالك', 'يوم']))
      .toEqual(['الحمد', 'لله', 'مالك', 'يوم'])
  })

  it('counts a word spelled two ways as one word', () => {
    expect(joinWindows(['ٱلرَّحْمَٰنِ'], ['الرحمن', 'الرحيم']))
      .toEqual(['ٱلرَّحْمَٰنِ', 'الرحيم'])
  })

  it('has nothing to join when one side is empty', () => {
    expect(joinWindows([], ['الله'])).toEqual(['الله'])
    expect(joinWindows(['الله'], [])).toEqual(['الله'])
  })

  it('leaves a page following the joined words unchanged by the join', () => {
    const windows = [SPOKEN.slice(0, 6), SPOKEN.slice(4, 10), SPOKEN.slice(8)]
    const joined = windows.reduce(joinWindows, [])
    expect(joined).toEqual(SPOKEN)
    expect(follow(PAGE, joined, { ended: true }).words.every((w) => w.state === SAID)).toBe(true)
  })
})

describe('a word cut in two by the machine', () => {
  // Measured against Deepgram: at a pause it ends its reading mid-word, so
  // العالمين arrived as العالم then مين. That is the engine's seam and not the
  // reciter's mistake, and it can fall inside any word, which is why it is a
  // rule about pieces and not a list of words.
  it('reads two pieces that spell the word as the word', () => {
    const heard = ['اهدنا', 'الصراط', 'المستق', 'يم', ...SPOKEN.slice(3)]
    expect(statesOf(PAGE, heard)).toEqual(PAGE.map(() => SAID))
    expect(follow(PAGE, heard, { ended: true }).extras).toEqual([])
  })

  it('still says where the reciter is after a cut word', () => {
    expect(follow(PAGE, ['اهدنا', 'الص', 'راط'], { ended: true }).at).toBe(2)
  })

  it('does not join two pieces that spell something else', () => {
    // غير and المغضوب next to each other are two words, not one; joining
    // anything that merely sits side by side would hide real mistakes.
    const heard = ['اهدنا', 'الصراط', 'المستقيم', 'صراط', 'الذين', 'أنعمت', 'عليهم', 'غيرالمغضوب']
    expect(statesOf(PAGE, heard)[7]).not.toBe(SAID)
  })
})

describe('weighing in the ear at each checking level', () => {
  // Four words as the page marked them: said, wrong, missed, not reached.
  const marks = {
    at: 3,
    words: [
      { word: 'a', state: SAID, heard: '' },
      { word: 'b', state: WRONG, heard: 'x' },
      { word: 'c', state: MISSED, heard: '' },
      { word: 'd', state: WAITING, heard: '' },
    ],
  }
  const states = (sure, level) => bySound(marks, sure, level).words.map((w) => w.state)

  it('softens an accusation the ear never checked into doubt', () => {
    expect(states([], 'standard')).toEqual([SAID, CHECK, CHECK, WAITING])
  })

  // The two levels are one dial: how little sureness it takes before doubt
  // becomes blame. Beginner blames under seven tenths, standard under 0.95, and
  // the step up marks more right words as well as more real slips.
  it('beginner blames under seven tenths and shows orange up to nine', () => {
    expect(states([0.05, 0.8, 0.5, 1], 'beginner')).toEqual([WRONG, CHECK, MISSED, WAITING])
    expect(states([0.8, 0.4, 0.1], 'beginner')).toEqual([SAID, WRONG, MISSED, WAITING])
  })

  it('standard blames under 0.95, a said word too, and leaves no orange band', () => {
    expect(states([0.93, 1, 0.5, 0], 'standard')).toEqual([WRONG, SAID, MISSED, WAITING])
    expect(states([0.95, 0.94], 'standard')).toEqual([SAID, WRONG, CHECK, WAITING])
  })

  it('a said word blamed on sound names no word, because the transcript heard it right', () => {
    expect(bySound(marks, [0.1], 'standard').words[0]).toEqual({ word: 'a', state: WRONG, heard: '' })
  })

  it('a word passed on sound shows no misheard word under it', () => {
    expect(bySound(marks, [1, 1], 'standard').words[1]).toEqual({ word: 'b', state: SAID, heard: '' })
  })

  it('a doubtful word never names a word', () => {
    // The orange "← بسم" beside a perfectly recited ٱلرَّحِيمِ came from here.
    for (const level of ['beginner', 'standard']) {
      for (const sure of [[], [1, 0.7], [1, 0.95], [0.5, 0.5]]) {
        for (const word of bySound(marks, sure, level).words) {
          if (word.state === CHECK) expect(word.heard).toBe('')
        }
      }
    }
  })

  it('only a word the ear checked and failed is called wrong', () => {
    const red = bySound(marks, [], 'standard').words.filter((w) => w.state === WRONG || w.state === MISSED)
    expect(red).toEqual([])
  })

  it('an unknown level is read as standard', () => {
    expect(states([0.05, 0.6], 'nonsense')).toEqual(states([0.05, 0.6], 'standard'))
  })
})
