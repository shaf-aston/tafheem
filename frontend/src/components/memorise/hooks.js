/** Memorise's state, one hook per job, for MemorisePanel to read. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useQueries, useQuery, useQueryClient } from '@tanstack/react-query'

import { getSimilar, getSimilarSurah } from '../../api'
import { BOOKS, bookPartQuery, bookPartsQuery, DEFAULT_BOOK } from '../../lib/books'
import {
  blanksFor, CHOICES, DEFAULT_DIFFICULTY, DIFFICULTIES, fromMemory, makeRandom,
  optionsFor, pagesOf, wordsOf,
} from '../../lib/memorise'
import { closestSpans, flagsOnPage, twinKeys } from '../../lib/similar'
import { readViewParam, writeViewParams } from '../../lib/tabUrl'
import { useSlide, useSwipe } from '../../lib/useSwipe'
import { scrollToEl } from '../../lib/scrollToEl'
import { useReciting } from '../../lib/useReciting'
import { useSetting } from '../../lib/settings'
import { warm } from '../../lib/warm'
import { useArrivalEffect } from '../../lib/useArrival'
import recite from '../../recite.json'

// The setting itself, not a copy of one of its numbers. Every id here comes
// from DIFFICULTIES, so a miss means memorise.json names a default that is not
// in its own list, and that should stop the page rather than quietly deal a
// share nobody chose.
export const difficultyOf = (id) => DIFFICULTIES.find((d) => d.id === id)

// What "Hidden" means while reciting. The same setting the page opens on, so
// choosing it and choosing it in typing mode leave the page in one state.
export const HIDDEN = DEFAULT_DIFFICULTY

// A line's label carries the part it is in, so "3:158" repeats a surah the
// control beside it already names. Inside that surah the number alone says it.
// A book whose lines are not numbered this way is left exactly as it is.
export const withinPart = (label) => label.split(':').pop()

// How long a finished page stays up, marked, before the next one turns in.
const TURN_AFTER_MS = recite['turn-after-s'] * 1000

// A page as a step on the back arrow's path: its first line, "2:6", with the
// book in front when it is not the Qur'an, "jazariyya/3:12".
const PLACE = /^(?:([a-z]+)\/)?(\d+):(\d+)$/
const placeOf = (bookId, part, line) => `${bookId === DEFAULT_BOOK ? '' : `${bookId}/`}${part}:${line.id}`

// Two ways to answer the same gap. Typing is recall; choosing is recognition,
// which is easier, and the only one that works without an Arabic keyboard.
export const WAYS = [
  { id: 'type', label: 'Type it' },
  // The count is read, never typed: "Pick from four" would start lying the day
  // option-count changes.
  { id: 'pick', label: `Pick from ${CHOICES}` },
  // Neither recall nor recognition: saying it, with the page following along.
  // Nothing is taken out here, so the whole page is shown.
  { id: 'recite', label: 'Recite it' },
  // Only the words that tell a verse from its twin are taken out, typed like
  // any other gap. Offered only by a book that has twins to show.
  { id: 'similar', label: 'Similar verses', onlyIf: (book) => book.similar },
]

/** What has been answered, whether the page is marked, and the words shown. */
export function useAnswers() {
  const [answers, setAnswers] = useState({})
  const [checked, setChecked] = useState(false)
  // Words uncovered by asking rather than by saying them. Kept apart from the
  // marks for exactly that reason: being shown a word is not reciting it.
  const [shown, setShown] = useState(() => new Set())
  // Anything that changes which words are missing starts the attempt over.
  // Done here, where the reader asks for the change, rather than by watching
  // the gaps afterwards, a watcher would also fire on the first render and
  // clear a page nobody had touched yet.
  const fresh = () => {
    setAnswers({})
    setChecked(false)
    setShown(new Set())
  }
  return { answers, setAnswers, checked, setChecked, shown, setShown, fresh }
}

/** How the reader answers and how much is missing. */
export function useHowYouAnswer(fresh) {
  const [difficulty, setDifficulty] = useState(DEFAULT_DIFFICULTY)
  // Bumped to deal a fresh set of gaps over the same page.
  const [deal, setDeal] = useState(1)
  // In the address as mode=, so a link (the landing page's "Recite, be heard")
  // can open the page already reciting.
  const [way, setWay] = useState(() => readViewParam('mode', WAYS.map((w) => w.id)) ?? 'type')
  useEffect(() => { writeViewParams({ mode: way === 'type' ? '' : way }) }, [way])
  const similar = way === 'similar'
  // Reciting from memory covers the page rather than sampling it, so which
  // words are missing is a different question there and not a harder setting
  // of the same one; lib/memorise.js says why. The word to start on is only
  // ever a word of this page, so a shorter page cannot leave it pointing off
  // the end.
  const hidden = way === 'recite' && difficulty !== 'none'
  const chooseDifficulty = (id) => { setDifficulty(id); fresh() }
  const reDeal = () => { setDeal((n) => n + 1); fresh() }
  const chooseWay = (id) => { setWay(id); fresh() }
  return { way, setWay, similar, hidden, difficulty, deal, chooseDifficulty, reDeal, chooseWay }
}

/** The book, part and page open, the word started on, and the moves between places. */
export function useBookPage({ fresh, setWay }) {
  const [bookId, setBookId] = useState(DEFAULT_BOOK)
  // What the reader picked, which is nothing until they pick; the part
  // actually open is derived below, once the book has said what its parts are.
  const [chosen, setChosen] = useState(null)
  const [pageNumber, setPageNumber] = useState(0)
  const [meaning, setMeaning] = useState(BOOKS[DEFAULT_BOOK].meaningDefault ?? false)
  // The word the reader pressed to start on, or null for "they did not say".
  // A page is not always begun at its top: somebody revising picks up where
  // they stopped, or goes back over the one ayah they keep losing. It is
  // pressed on the word itself, so there is no control to find; and when it is
  // not pressed at all, the recitation says where it began and the page
  // follows that instead. Pressing always wins, because a reader who has said
  // where they are is not to be argued with by a microphone.
  const [pinned, setPinned] = useState(null)

  const book = BOOKS[bookId]

  // What this book breaks into. Asked for rather than listed, because a poem's
  // baabs are headings inside the poem, the same fetch the verses come from,
  // so asking costs nothing after the first time.
  const { data: parts } = useQuery(bookPartsQuery(bookId))

  // The part actually open: what the reader picked, as long as it is one of
  // this book's. Read from the parts rather than copied into state, so the
  // first part opens on arrival and switching books cannot leave the previous
  // book's part selected for a render.
  const part = parts?.some((p) => p.id === chosen) ? chosen : (parts?.[0]?.id ?? null)

  const { data, isPending, isError, error, refetch } = useQuery({ ...bookPartQuery(bookId, part), enabled: part !== null })

  // The parts either side are where a reader goes next.
  const client = useQueryClient()
  useEffect(() => {
    const at = parts?.findIndex((p) => p.id === part) ?? -1
    if (at >= 0) [parts[at - 1], parts[at + 1]].forEach((p) => p && warm(client, bookPartQuery(bookId, p.id)))
  }, [client, parts, part, bookId])

  const pages = useMemo(() => (data ? pagesOf(data.lines, book.wordsPerPage) : []), [data, book])
  const page = pages[pageNumber] ?? null

  // A new page, book or part is a new place, so the last one's starting word
  // means nothing on it. Changing the starting word itself also starts over,
  // because it moves what is covered.
  const openAt = (at) => { setPinned(at); fresh() }
  const openPart = (id, n = 0) => { setChosen(id); setPageNumber(n); setPinned(null); fresh() }
  const openPage = (n) => { setPageNumber(n); setPinned(null); fresh() }
  // Switching books starts over at that book's own first part and its own
  // meaning-shown default, the Qur'an's "off by default" is not a preference
  // to carry across to a book most readers cannot already recite from memory.
  const openBook = (id) => {
    setBookId(id)
    setChosen(null)
    setPageNumber(0)
    setPinned(null)
    setMeaning(BOOKS[id].meaningDefault ?? false)
    if (!BOOKS[id].similar) setWay((was) => (was === 'similar' ? 'type' : was))
    fresh()
  }
  // The pages of a part, fetched (or cached), and which holds a line (-1 for none).
  const pageOfLine = (b, partId, lineId) => client.fetchQuery(bookPartQuery(b, partId)).then(({ lines }) => {
    const all = pagesOf(lines, BOOKS[b].wordsPerPage)
    return [all.findIndex((p) => p.some((line) => line.id === lineId)), all]
  })
  return {
    bookId, book, parts, part, data, isPending, isError, error, refetch, pages, page, pageNumber, meaning, setMeaning, pinned,
    openAt, openPart, openPage, openBook, pageOfLine,
  }
}

/** Stepping a page either way, across parts, by button or swipe. */
export function usePageSteps({ parts, part, pages, pageNumber, bookId, pageOfLine, openPage, openPart }) {
  // The part `by` either side of this one: past a surah's last page is the next
  // surah, before its first is the one before.
  const partBy = (by) => parts?.[parts.findIndex((p) => p.id === part) + by]
  const stepPage = (by) => {
    const n = pageNumber + by
    if (n >= 0 && n < pages.length) return openPage(n)
    const next = partBy(by)
    if (by > 0) return openPart(next.id, 0)
    pageOfLine(bookId, next.id).then(([, all]) => openPart(next.id, all.length - 1)).catch(() => {})
  }
  const atStart = pageNumber === 0 && !partBy(-1)
  const atEnd = pageNumber >= pages.length - 1 && !partBy(1)
  const swipe = useSwipe(!atStart && (() => stepPage(-1)), !atEnd && (() => stepPage(1)))
  // Where the page falls in the book, so a step either way slides in from its own side.
  const slide = useSlide((parts?.findIndex((p) => p.id === part) ?? 0) * 10000 + pageNumber)
  return { partBy, stepPage, atStart, atEnd, swipe, slide }
}

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
      lines.push({ key: line.label, label: withinPart(line.label), from: words.length, count: said.length })
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
    for (let at = Math.max(reciting.marks.at, startFrom + 1); at < recitedPage.words.length; at += 1) {
      if (!shown.has(at) && reciting.marks.words[at]?.state === 'waiting') return at
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

/** Which ayahs of this surah have a twin, and the twins of the ones on this page. */
function useTwins({ part, page, similar }) {
  // Asked only in this mode, and only for ayahs that have one.
  const twinsOfSurah = useQuery({
    queryKey: ['similar-surah', part],
    queryFn: () => getSimilarSurah(part),
    enabled: similar && part !== null,
    staleTime: Infinity,
  })
  const twinned = useMemo(() => twinKeys(twinsOfSurah.data?.groups), [twinsOfSurah.data])
  const twinLines = useMemo(
    () => (page ?? []).map((line, l) => ({ line, l })).filter(({ line }) => twinned.has(line.label)),
    [page, twinned],
  )
  const twinQueries = useQueries({
    queries: twinLines.map(({ line }) => {
      const [surah, ayah] = line.label.split(':').map(Number)
      return { queryKey: ['similar', surah, ayah], queryFn: () => getSimilar(surah, ayah), staleTime: Infinity }
    }),
  })
  // The query array is new every render, so the gaps are keyed on when each
  // answer last arrived instead.
  const twinData = twinQueries.map((q) => q.data)
  const twinStamp = twinQueries.map((q) => q.dataUpdatedAt).join()
  return { twinsOfSurah, twinned, twinLines, twinQueries, twinData, twinStamp }
}

/** Which words are missing, the options offered for them, and the twins behind the similar mode. */
export function useGaps({ data, page, part, pageNumber, deal, difficulty, way, similar, hidden, startFrom }) {
  const { twinsOfSurah, twinned, twinLines, twinQueries, twinData, twinStamp } = useTwins({ part, page, similar })

  // The gaps depend on the page, the difficulty and the deal; and on nothing
  // else, so typing an answer never moves them.
  const blanks = useMemo(
    () => {
      if (!page) return new Set()
      if (similar) {
        const gaps = new Set()
        twinLines.forEach(({ line, l }, i) => {
          const words = wordsOf(line.arabic)
          const flags = flagsOnPage(words, twinData[i]?.text ?? '', closestSpans(twinData[i]?.text ?? '', twinData[i]?.partners))
          flags.forEach((on, w) => { if (on) gaps.add(`${l}:${w}`) })
        })
        return gaps
      }
      if (hidden) return fromMemory(page, startFrom)
      return blanksFor(page, difficultyOf(difficulty).share, makeRandom(pageNumber * 131 + deal))
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [page, hidden, similar, twinLines, twinStamp, startFrom, difficulty, pageNumber, deal],
  )

  // Every word of the whole part, not just this page: three wrong options taken
  // from four ayahs away are still words the reader has been reading, and a
  // short page would otherwise have nothing to offer.
  const pool = useMemo(
    () => (data ? data.lines.flatMap((line) => wordsOf(line.arabic)) : []),
    [data],
  )

  // Worked out once per set of gaps so that answering one never reshuffles the
  // others. Each gap gets its own seed, or every gap on the page would offer
  // its words in the same order.
  const choices = useMemo(() => {
    if (!page || way !== 'pick') return null
    const map = new Map()
    let nth = 0
    for (const key of [...blanks].sort()) {
      const [l, w] = key.split(':').map(Number)
      nth += 1
      map.set(key, optionsFor(wordsOf(page[l].arabic)[w], pool, makeRandom(deal * 977 + nth)))
    }
    return map
  }, [page, blanks, pool, way, deal])
  return { blanks, choices, twinsOfSurah, twinned, twinLines, twinQueries }
}

/** The microphone and the page turning under it: stopping, forgetting, carrying on, and reciting from elsewhere. */
export function useReciteTurns({ way, hidden, reciting, recitedPage, bookId, part, pageNumber, pinned, pages, partBy, openPart, pageOfLine }) {
  // Whether recording again carries on the same recitation or begins the page
  // afresh. The reader's own choice, in the settings panel, because both are
  // reasonable: one person paused to look a word up, another gave up.
  const resume = useSetting('resume-reciting')
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
  const card = useRef(null)
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
    if (way !== 'recite' || !listening || !reciting.finished) return
    const timer = setTimeout(turnPage, TURN_AFTER_MS)
    return () => clearTimeout(timer)
  }, [way, listening, reciting.finished])  // eslint-disable-line react-hooks/exhaustive-deps
  return { card, listen, elsewhere, where, askToGo, goElsewhere, setStayed }
}

/**
 * Each page opened is a step the back arrow returns to; a step returned to,
 * or handed over from another tab, opens its page here.
 * The page landed on is that step already, even when the step named a later
 * line on it ("2:255" opens the page from 2:250): recording it again would
 * push a new step and trap the back arrow there.
 */
export function useArrivedPage({ arrival, incoming, onVisit, bookId, part, page, pageOfLine, openBook, openPart }) {
  const arriving = useRef(false)
  const landed = useRef(null)
  useArrivalEffect(arrival, () => {
    const [, b = DEFAULT_BOOK, p, line] = PLACE.exec(incoming ?? '') ?? []
    if (!p || !BOOKS[b]) return
    arriving.current = true
    pageOfLine(b, Number(p), Number(line)).then(([n, all]) => {
      const at = Math.max(n, 0)
      landed.current = placeOf(b, Number(p), all[at][0])
      if (b !== bookId) openBook(b)
      openPart(Number(p), at)
    }).catch(() => {}).finally(() => { arriving.current = false })
  })
  const here = page && placeOf(bookId, part, page[0])
  useEffect(() => {
    if (!here || arriving.current || here === landed.current) return
    landed.current = null
    onVisit?.(here)
  }, [here])  // eslint-disable-line react-hooks/exhaustive-deps
}
