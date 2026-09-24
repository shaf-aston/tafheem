/**
 * Following somebody as they recite: what is on the page, what came back from
 * the microphone, and where those two part company.
 *
 * In: the words of the page, and every word heard so far. Out: where the
 * reciter is, and one state for every word on the page. Pure, so no React, no
 * microphone and no network reach it, and every hard case is a list of strings
 * in follow.test.js.
 *
 * Worked out fresh every time rather than carried along
 * -----------------------------------------------------
 * What the engine heard changes as it hears more: a word comes back wrong and
 * comes back right once the words after it are in. So this keeps nothing
 * between calls and lines the whole thing up again each time. The same words in
 * gives the same answer out, always, which is what makes it testable and what
 * stops a wrong guess from sticking around after the evidence for it is gone.
 *
 * Why lining up, and not walking a pointer forward
 * ------------------------------------------------
 * A pointer that steps to the next word cannot tell a wrong word from an added
 * one until it sees what comes after: وَمَا said in place of وَلَا looks exactly
 * like وَمَا added in front of وَلَا. So the whole thing is lined up at once,
 * cheapest reading wins, and recite.json's costs are what "cheapest" means. One
 * wrong word costs less than losing a word and gaining one, so it is read as
 * one mistake rather than two; a near miss costs almost nothing, so doubt
 * always beats an accusation.
 *
 * Where they began, worked out rather than asked for
 * --------------------------------------------------
 * `startAt` is what the reader said they would start on. It is not always
 * true: somebody opens a page and simply recites, from wherever they had got
 * to. The cheapest reading already answers this without being asked, because
 * the first page word it pairs with a word heard is, by construction, the word
 * they began on. That is given back as `began`, under the same two guards as
 * every other claim here: nothing is said until enough of this page has been
 * heard to be sure it is this page, and nothing is said about a pairing too
 * new to have settled. Until then it is null, which means "not yet known" and
 * never "the top of the page".
 *
 * Nothing is marked the moment it is said
 * ---------------------------------------
 * A word holds plain until `settle-words` more words have gone past it. Being
 * right shows at once, because that is not a mark and nobody is accused by it;
 * being wrong waits, because that is the claim that has to be right. `ended`
 * settles everything, which is what the pause at the end of an ayah is for.
 *
 * How much to hand it
 * -------------------
 * One page of words and the words heard on that page. Lining up is the length
 * of one multiplied by the other, which is nothing at a page and a minute, and
 * would be something after an hour, so an hour of reciting is many calls of one
 * page each and never one call of the lot.
 */
import config from '../recite.json'
import { sameSpokenWord } from './arabicText'
import { soundsTheSame } from './soundalike'

/** Not reached yet, or not yet sure enough to say. Shown plain. */
export const WAITING = 'waiting'
/** Said, and right. */
export const SAID = 'said'
/** Two different words that sound the same: a slip, or a mishearing. Orange. */
export const CHECK = 'check'
/** A different word. Red. */
export const WRONG = 'wrong'
/** A word on the page that was never said. Red outline. */
export const MISSED = 'missed'

const COSTS = config.costs

/** What it costs to read `said` as the page's `printed`, and what that is. */
const asMatch = (said, printed) => {
  if (sameSpokenWord(said, printed)) return [0, SAID]
  if (soundsTheSame(said, printed)) return [COSTS.near, CHECK]
  return [COSTS.wrong, WRONG]
}

/**
 * The cheapest reading of the whole thing, as a list of steps in order.
 *
 * Each step is one of: a page word and a heard word together, a page word made
 * of two heard pieces, a page word with nothing said for it, or a heard word
 * with nothing on the page for it. Page words after the last step are simply
 * not reached yet, and cost nothing: the reciter is in the middle of the page,
 * not skipping its end.
 */
const lineUp = (page, heard, startAt) => {
  const cost = []
  const from = []
  for (let i = 0; i <= page.length; i += 1) {
    cost.push(new Array(heard.length + 1).fill(0))
    from.push(new Array(heard.length + 1).fill(null))
  }

  // Nothing heard yet: every page word from where reciting began is a word not
  // said. Before that point they are free, because somebody who opened the page
  // halfway down never claimed to have said the words above.
  //
  // A null startAt means nobody said where they began, and then every leading
  // word is free. Charging for them instead is what made a recitation started
  // near the foot of a long page cost more to line up than to throw away: nine
  // skipped words at three each is dearer than calling three real words extra
  // at five, so the whole thing was read as not being this page at all.
  for (let i = 1; i <= page.length; i += 1) {
    cost[i][0] = cost[i - 1][0] + (startAt === null || i <= startAt ? 0 : COSTS.missed)
    from[i][0] = MISSED
  }
  // Heard before the page begins is a word said that is not in the book.
  for (let j = 1; j <= heard.length; j += 1) {
    cost[0][j] = cost[0][j - 1] + COSTS.extra
    from[0][j] = 'extra'
  }

  for (let i = 1; i <= page.length; i += 1) {
    for (let j = 1; j <= heard.length; j += 1) {
      const [together] = asMatch(heard[j - 1], page[i - 1])
      let best = cost[i - 1][j - 1] + together
      let step = 'together'

      const missed = cost[i - 1][j] + COSTS.missed
      if (missed < best) { best = missed; step = MISSED }

      const extra = cost[i][j - 1] + COSTS.extra
      if (extra < best) { best = extra; step = 'extra' }

      // Two pieces that spell this word are this word. An engine cuts its
      // reading wherever the reciter drew breath, and a breath can land inside
      // a word, so العالمين arrives as العالم then مين. Only ever allowed when
      // the pieces put together really are the printed word, which is why it
      // may cost so little without inviting itself in.
      if (j >= 2 && sameSpokenWord(heard[j - 2] + heard[j - 1], page[i - 1])) {
        const joined = cost[i - 1][j - 2] + COSTS.split
        if (joined < best) { best = joined; step = 'joined' }
      }

      cost[i][j] = best
      from[i][j] = step
    }
  }

  // Every word heard has to be accounted for; how far down the page that
  // leaves the reciter is whatever costs least. Ties go to the earlier one, so
  // words that were never reached stay unreached rather than being called
  // missed.
  let end = 0
  for (let i = 1; i <= page.length; i += 1) {
    if (cost[i][heard.length] < cost[end][heard.length]) end = i
  }

  const steps = []
  let i = end
  let j = heard.length
  while (i > 0 || j > 0) {
    const step = from[i][j]
    if (step === 'together') { steps.push({ step, i: i - 1, j: j - 1 }); i -= 1; j -= 1 }
    else if (step === 'joined') { steps.push({ step, i: i - 1, j: j - 1 }); i -= 1; j -= 2 }
    else if (step === MISSED) { steps.push({ step, i: i - 1, j }); i -= 1 }
    else { steps.push({ step, i, j: j - 1 }); j -= 1 }
  }
  return { steps: steps.reverse(), at: end }
}

/**
 * The words in a reading, as words: no ayah numbers, no full stops.
 *
 * An engine writes ordinary prose, so it ends a sentence with a full stop and
 * that stop arrives stuck to the last word. Left on, ٱلضَّآلِّينَ against
 * "الضالين." is a difference of spelling being reported as a mistake, so
 * anything that is not an Arabic letter is dropped before the word is compared.
 */
export const wordsHeard = (text) => (text ?? '')
  .split(/\s+/)
  // Arabic and nothing else, which keeps every mark a word is written with and
  // drops the stops, brackets and numbers around it.
  .map((word) => word.replace(/[^\p{Script=Arabic}]/gu, ''))
  .filter(Boolean)

/**
 * Whether a reading has anything of this page in it.
 *
 * A reading of silence is not empty: the engine writes something, and with
 * music in the room it writes موسيقى. One window of that, arriving after the
 * reciter has finished, was reported as a word added to al-Fatihah. A reading
 * with not one word of the page in it is not this page being recited, so it is
 * left out rather than argued with.
 */
export const isOfPage = (words, page) =>
  words.some((word) => page.some((printed) => sameSpokenWord(word, printed)))

/**
 * Everything heard so far, with the newest window of sound added on the end.
 *
 * Each window holds the last seconds of sound, so it starts with the end of the
 * window before it: ten seconds read every eight means two seconds said twice.
 * Those repeats are the machine's, not the reciter's, and letting them through
 * would report somebody as having added words they never said. So the longest
 * run where the end of what we have is the start of what just arrived is
 * treated as one, and only what is past it is kept.
 *
 * The old words are left as they were. A window that spells an earlier word
 * differently is not evidence enough to rewrite what has already settled, and
 * the words themselves are compared with `sameSpokenWord`, so a difference of
 * spelling is not a difference of word.
 */
export const joinWindows = (heard, window) => {
  const most = Math.min(heard.length, window.length)
  for (let run = most; run > 0; run -= 1) {
    const overlaps = Array.from({ length: run }).every((_, k) =>
      sameSpokenWord(heard[heard.length - run + k], window[k]))
    if (overlaps) return [...heard, ...window.slice(run)]
  }
  return [...heard, ...window]
}

/**
 * Where the reciter is and how every word on the page stands.
 *
 * `page` and `heard` are lists of words in the order they are printed and in
 * the order they were heard. `startAt` is the page word reciting began on, so
 * an ayah opened halfway down a page does not report the words above it as
 * skipped; null means nobody said, and then the words above wherever they turn
 * out to have begun are not skipped either. `ended` says the reciter has
 * stopped, which settles every mark that was still waiting for more words.
 *
 * Gives back `at`, the page word expected next; `began`, the page word they
 * actually started on or null while that is not yet known; `words`, one state
 * and any misheard word for each word of the page; `extras`, words said that
 * are not in the book, each with the page word it came after; and `started`,
 * false while too little of this page has been heard for any of it to be worth
 * marking.
 */
export const follow = (page, heard, { startAt = 0, ended = false, settle = config['settle-words'] } = {}) => {
  const words = page.map((word) => ({ word, state: WAITING, heard: '' }))
  const extras = []
  if (!page.length) return { at: 0, began: null, words, extras, started: false }

  const { steps, at } = lineUp(page, heard, startAt)

  // Nothing is said about a page nobody has started reciting. Sound in a room
  // is not a recitation: with music playing, the engine returned موسيقى, every
  // one of those words was lined up against the page, and it showed twelve
  // mistakes made by somebody who had not yet opened their mouth. So until
  // enough words of this page have actually been heard, the page holds plain.
  const found = steps.filter(({ step, i, j }) =>
    step === 'joined' || (step === 'together' && asMatch(heard[j], page[i])[1] !== WRONG)).length
  if (found < config['anchor-words']) return { at: startAt ?? 0, began: null, words, extras, started: false }
  // A mark may only be shown once this many words have gone past it. `ended`
  // means no more are coming, so waiting any longer would never settle.
  const settled = (j) => ended || heard.length - j > settle

  // The first page word paired with something heard: where they began. Only a
  // pairing that has settled counts, so a word that momentarily lined up with
  // noise at the top of the page cannot claim to be the start and then quietly
  // change its mind once the real words arrive.
  const first = steps.find(({ step, i, j }) =>
    settled(j) && (step === 'joined' || (step === 'together' && asMatch(heard[j], page[i])[1] !== WRONG)))
  const began = first ? first.i : null

  let lastSaid = -1
  for (const { step, i, j } of steps) {
    // Said, in pieces, and right. Nothing is shown of the seam: the reciter did
    // not make it and has nothing to correct.
    if (step === 'joined') {
      words[i] = { word: page[i], state: SAID, heard: '' }
      lastSaid = i
      continue
    }

    if (step === 'together') {
      const [, state] = asMatch(heard[j], page[i])
      // Right shows at once. Wrong waits: it is the claim that has to be right.
      words[i] = {
        word: page[i],
        state: state === SAID || settled(j) ? state : WAITING,
        heard: state === SAID || !settled(j) ? '' : heard[j],
      }
      lastSaid = i
      continue
    }

    // A word on the page with nothing said for it. Only from where reciting
    // began: above that nobody claimed anything, whether they said where they
    // were starting or it was worked out from what they recited.
    if (step === MISSED) {
      if (i >= (startAt ?? began ?? 0) && settled(j)) words[i] = { word: page[i], state: MISSED, heard: '' }
      continue
    }

    // Said, and left over. Only a word that is nowhere on the page is a word
    // added: a word that is on it has been said twice, and saying a word twice
    // is not a mistake, whether the reciter went back over a phrase or the
    // engine returned the same words in two readings. A real recitation of
    // al-Fatihah reported fifteen added words this way before this rule was
    // written the simple way.
    const onThePage = page.some((word) => sameSpokenWord(heard[j], word))
    if (!onThePage && settled(j)) extras.push({ after: lastSaid, heard: heard[j] })
  }

  return { at, began, words, extras, started: true }
}

/**
 * The marks, with the ear's sureness weighed in at the reader's checking level.
 *
 * `sure` holds, per page word, how likely the ear found that word in the sound
 * (0 to 1). Lining up words compares letters only, so it passes a word said
 * with the wrong vowel and fails a right word the ear wrote down wrong.
 * Sureness is judged on sound, and the level in recite.json says how far to
 * trust it either way. A waiting word stays waiting.
 *
 * Two things this will not do, both of them a lie the page used to tell
 * ---------------------------------------------------------------------
 * A doubtful word never names a word. Orange means "I cannot tell", and the
 * word beside it came from the transcript, which is the part that was wrong in
 * the first place: a perfect بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ showed
 * "← بسم" against ٱلرَّحِيمِ, asserting a word nobody claims was said there.
 *
 * And a word the sound never checked is never accused. Measured on the 1,950
 * marked recordings in backend/data/recitation_checks, the transcript alone
 * marks 10.6% of correctly recited words; the check by sound is the only part
 * of this that earns a red. With no score, an accusation softens to doubt.
 *
 * So a word the transcript found is still red when the sound says it was not
 * said right: a wrong vowel has the same letters, and the transcript cannot see
 * it. Measured on 390 marked recordings heard by Groq, at 0.9 this caught
 * 58% of vowel slips where needing the transcript to miss too caught 16%, for
 * 3.3% of right words marked against 2.0%; standard now sits at 0.95 (backend/scripts/sweep_sureness.py).
 */
export const bySound = (marks, sure, level) => {
  const rule = config.levels[level] ?? config.levels.standard
  const words = marks.words.map((mark, i) => {
    const s = sure[i]
    if (mark.state === WAITING || mark.state === SAID) {
      if (s == null || mark.state === WAITING) return mark
      if (s < rule['flag-below']) return { ...mark, state: WRONG, heard: '' }
      return s < rule['doubt-below'] ? { ...mark, state: CHECK, heard: '' } : mark
    }
    if (s == null) return { ...mark, state: CHECK, heard: '' }
    if (s >= rule['pass-sure']) return { ...mark, state: SAID, heard: '' }
    if (s < rule['flag-below']) return mark
    return { ...mark, state: CHECK, heard: '' }
  })
  return { ...marks, words }
}
