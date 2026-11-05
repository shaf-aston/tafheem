/**
 * Reciting a page from memory, the hooks MemorisePanel reads for it:
 *
 *   useReciteState  the page as words to recite, and the ear following them
 *   useReciteTurns  the microphone and the page turning under it
 *   useOpenCard     which reached word or ayah has its card open
 *
 * The rest of Memorise's state (book, page, gaps) is in ./hooks.
 */
import { useEffect, useMemo, useRef, useState } from 'react'

import { ayahAt, wordsOf } from '../../lib/memorise/memorise'
import { scrollToEl } from '../../lib/motion/scrollToEl'
import { WAITING } from '../../lib/recite/follow'
import { useReciting } from '../../lib/recite/useReciting'
import { useSetting } from '../../lib/store/settings'
import config from '../../config/memorise.json'

import { withinPart } from './hooks'

// How long a finished page stays up, marked, before the next one turns in.
const TURN_AFTER_MS = config['turn-after-s'] * 1000

/** The page as words to recite, the follower listening to them, and the words asked for. */
export function useReciteState({ page, book, pinned, shown, setShown }) {
  // The page as one run of words, which is how somebody recites it and so how
  // the follower reads it. Each line remembers where it starts in that run, so
  // a mark can be put back on the word it belongs to.
  const recitedPage = useMemo(() => {
    const words = []
    const lines = []
    for (const line of page ?? []) {
      const said = wordsOf(line.arabic)
      lines.push({ ...ayahAt(line.label, said, words.length), label: withinPart(line.label) })
      words.push(...said)
    }
    return { words, lines }
  }, [page])

  // Nothing is told to the follower that the reader did not say. Left unasked
  // it works the start out of the recitation itself, and reports it as began.
  const reciting = useReciting(recitedPage.words, {
    startAt: pinned,
    ayahs: book.checkedBySound ? recitedPage.lines : [],
  })
  // Where the page is being recited from: what the reader pressed, else what
  // the recitation showed, else the top, which is where a page not yet recited
  // has to open so there is one word to begin from. Derived, never stored, so
  // there is no moment where the two could disagree and nothing to reset.
  const startFrom = Math.min(
    pinned ?? reciting.marks.began ?? 0,
    Math.max(0, recitedPage.words.length - 1),
  )

  /**
   * The next word still covered, or -1 when there is none left.
   *
   * Where the follower says the reciter is, never before the word they started
   * on, and never a word already shown: pressing "show a word" twice has to
   * give two words, and the first press must not hand back the cue that was
   * already on the screen.
   */
  const nextCovered = () => {
    for (let at = Math.max(reciting.marks.at, pinned == null ? startFrom + 1 : startFrom); at < recitedPage.words.length; at += 1) {
      if (!shown.has(at) && reciting.marks.words[at]?.state === WAITING) return at
    }
    return -1
  }

  // Which ayah the page is being followed from, for saying so out loud. The
  // word is not named: a word repeats down a page and its ayah does not.
  const startLabel = recitedPage.lines.find(
    (one) => startFrom >= one.from && startFrom < one.from + one.count,
  )?.label ?? ''

  /** Uncover the next word, or the rest of the ayah it is in. */
  const show = (whole) => {
    const at = nextCovered()
    if (at < 0) return
    const line = recitedPage.lines.find((one) => at >= one.from && at < one.from + one.count)
    const upTo = whole && line ? line.from + line.count : at + 1
    setShown((was) => {
      const now = new Set(was)
      for (let i = at; i < upTo; i += 1) now.add(i)
      return now
    })
  }
  return { recitedPage, reciting, startFrom, startLabel, show }
}

/** The microphone and the page turning under it: stopping, forgetting, carrying on, and reciting from elsewhere. */
export function useReciteTurns({ card, way, hidden, reciting, recitedPage, bookId, part, pageNumber, pinned, pages, partBy, openPart, pageOfLine }) {
  // Whether recording again carries on the same recitation or begins the page
  // afresh. The reader's own choice, in the settings panel, because both are
  // reasonable: one person paused to look a word up, another gave up.
  const resume = useSetting('resume-reciting')
  const turnsItself = useSetting('turn-page-itself')
  const [stayed, setStayed] = useState(null)

  /**
   * Record. Carrying on keeps what was already heard, which is what somebody
   * who paused to look a word up is doing; the other reading of the same
   * button is starting the page again, and the setting says which.
   */
  const listen = () => {
    if (!resume) reciting.forget()
    setStayed(null)
    reciting.start()
  }

  // Leaving the page, or the way of answering, stops the microphone. Nothing
  // else in the app may leave one listening, and neither may this.
  const listening = reciting.listening
  useEffect(() => {
    if (listening && way !== 'recite') reciting.stop()
  }, [listening, way, reciting])
  // A page turned by the recitation itself carries on listening: set just
  // before it turns, read by the two effects below, and put down by the second.
  const turning = useRef(false)
  useEffect(() => () => { if (!turning.current) reciting.stop() }, [pageNumber, part, bookId])  // eslint-disable-line react-hooks/exhaustive-deps
  // Carrying on is only ever carrying on with the same page from the same
  // place. Move either and the words already heard were about somewhere else,
  // so they go, whatever the setting says.
  const forget = reciting.forget
  // Not on startFrom: that moves by itself the moment the recitation says
  // where it began, and forgetting then would throw away the very words that
  // said it. Only a place the reader chose, or a page they turned to.
  useEffect(() => {
    if (turning.current) { turning.current = false; return }
    forget()
  }, [forget, pageNumber, part, bookId, pinned])

  /**
   * Carry the recitation on to another page without stopping: the next one,
   * because the reciter reached the end of this one, or wherever in the
   * Qur'an they turned out to be. What was heard goes with the old page
   * (turn(), not forget(), so the recording under way is kept), and the new
   * page is followed from wherever they are on it.
   */
  const carryOnAt = (partId, n) => {
    if (partId === part && n === pageNumber) return
    turning.current = true
    reciting.turn()
    openPart(partId, n)
    scrollToEl(card.current, 'top')
  }
  const turnPage = () => {
    if (pageNumber + 1 < pages.length) return carryOnAt(part, pageNumber + 1)
    if (partBy(1)) carryOnAt(partBy(1).id, 0)
  }

  // Reciting from somewhere else in the Qur'an. Being tested on a page, the
  // reader is asked first, since leaving it is their call; just reciting,
  // the page follows them without asking.
  // An ayah on this very page is not elsewhere: the ear garbled it, and the
  // page already follows it.
  const elsewhere = reciting.elsewhere
    && !(part === reciting.elsewhere.surah
      && recitedPage.lines.some((line) => line.key === `${reciting.elsewhere.surah}:${reciting.elsewhere.ayah}`))
    ? reciting.elsewhere
    : null
  // A reading names a fresh place each time, so the place is followed by its
  // name, and Stay holds for the whole surah until reciting starts again.
  const where = elsewhere && `${elsewhere.surah}:${elsewhere.ayah}`
  const goElsewhere = () => pageOfLine(bookId, elsewhere.surah, elsewhere.ayah)
    .then(([n]) => { if (n >= 0) carryOnAt(elsewhere.surah, n) })
  useEffect(() => {
    if (elsewhere && way === 'recite' && listening && !hidden) goElsewhere()
  }, [where])  // eslint-disable-line react-hooks/exhaustive-deps
  const askToGo = elsewhere && elsewhere.surah !== stayed && way === 'recite' && listening && hidden
  // A moment on the finished page first, marks settled and weighed, so a
  // slip in its last ayah is seen before the page goes.
  useEffect(() => {
    if (way !== 'recite' || !listening || !reciting.finished || !turnsItself) return
    const timer = setTimeout(turnPage, TURN_AFTER_MS)
    return () => clearTimeout(timer)
  }, [way, listening, reciting.finished, turnsItself])  // eslint-disable-line react-hooks/exhaustive-deps
  return { listen, elsewhere, where, askToGo, goElsewhere, setStayed }
}

/**
 * The word or ayah whose card is open: { at } or { line }. Only a place; the
 * card reads the live marks, so what it shows keeps up with the recitation.
 * Closed by the reader, Esc or a press outside (MarkCard), and here by a page
 * turn or by stopping; never by a mark changing under it. A card is stamped
 * with the page and listening state it was opened in, and only counts while
 * they are unchanged.
 */
export function useOpenCard(stamp) {
  const [asked, setAsked] = useState(null)
  const open = asked?.stamp === stamp ? asked : null
  const setOpen = (place) => setAsked(place && { ...place, stamp })
  return [open, setOpen]
}
