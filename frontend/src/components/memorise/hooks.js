/** Memorise's state, one hook per job, for MemorisePanel to read. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { BOOKS, bookPartQuery, bookPartsQuery, DEFAULT_BOOK } from '../../lib/memorise/books'
import {
  blanksFor, CHOICES, DEFAULT_DIFFICULTY, DIFFICULTIES, fromMemory, makeRandom,
  optionsFor, pagesOf, wordsOf,
} from '../../lib/memorise/memorise'
import { readViewParam, writeViewParams } from '../../lib/nav/tabUrl'
import { useSlide, useSwipe } from '../../lib/motion/useSwipe'
import { scrollToEl } from '../../lib/motion/scrollToEl'
import { warm } from '../../lib/api/warm'
import { useArrivalEffect } from '../../lib/nav/useArrival'

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

// A page as a step on the back arrow's path: its first line, "2:6", with the
// book in front when it is not the Qur'an, "jazariyya/3:12".
const PLACE = /^(?:([a-z]+)\/)?(\d+):(\d+)$/
// The book, part and line a link names, or null for none (or a book that is not here).
const linkOf = (incoming) => {
  const [, book = DEFAULT_BOOK, part, line] = PLACE.exec(incoming ?? '') ?? []
  return part && BOOKS[book] ? { book, part: Number(part), line: Number(line) } : null
}
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
]

/** How the reader answers and how much is missing. */
export function useHowYouAnswer() {
  const [difficulty, setDifficulty] = useState(DEFAULT_DIFFICULTY)
  // Bumped to deal a fresh set of gaps over the same page.
  const [deal, setDeal] = useState(1)
  // In the address as mode=, so a link (the landing page's "Recite, be heard")
  // can open the page already reciting.
  const [way, setWay] = useState(() => readViewParam('mode', WAYS.map((w) => w.id)) ?? 'type')
  useEffect(() => { writeViewParams({ mode: way === 'type' ? '' : way }) }, [way])
  // Reciting from memory covers the page rather than sampling it, so which
  // words are missing is a different question there and not a harder setting
  // of the same one; lib/memorise/memorise.js says why. The word to start on is only
  // ever a word of this page, so a shorter page cannot leave it pointing off
  // the end.
  const hidden = way === 'recite' && difficulty !== 'none'
  return { way, setWay, hidden, difficulty, deal, chooseDifficulty: setDifficulty, reDeal: () => setDeal((n) => n + 1), chooseWay: setWay }
}

/**
 * The book, part and page open, the word started on, and the moves between places.
 * A page opened from a link starts on the link's book and part, so the surah it names is
 * what loads, not the first one and then that.
 */
export function useBookPage({ incoming }) {
  const [start] = useState(() => linkOf(incoming))
  const [bookId, setBookId] = useState(start?.book ?? DEFAULT_BOOK)
  // What the reader picked, which is nothing until they pick; the part
  // actually open is derived below, once the book has said what its parts are.
  const [chosen, setChosen] = useState(start?.part ?? null)
  const [pageNumber, setPageNumber] = useState(0)
  const [meaning, setMeaning] = useState(BOOKS[bookId].meaningDefault ?? false)
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
  // means nothing on it. The answers are not cleared here: they are kept under
  // the page's gaps (useAnswers), so going back finds them.
  const openAt = setPinned
  const openPart = (id, n = 0) => { setChosen(id); setPageNumber(n); setPinned(null) }
  const openPage = (n) => { setPageNumber(n); setPinned(null) }
  // Switching books starts over at that book's own first part and its own
  // meaning-shown default, the Qur'an's "off by default" is not a preference
  // to carry across to a book most readers cannot already recite from memory.
  const openBook = (id) => {
    setBookId(id)
    setChosen(null)
    setPageNumber(0)
    setPinned(null)
    setMeaning(BOOKS[id].meaningDefault ?? false)
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
export function usePageSteps({ card, parts, part, pages, pageNumber, bookId, pageOfLine, openPage, openPart, landing }) {
  // The part `by` either side of this one: past a surah's last page is the next
  // surah, before its first is the one before.
  const partBy = (by) => parts?.[parts.findIndex((p) => p.id === part) + by]
  const turned = useRef(false)
  const stepPage = (by) => {
    turned.current = true
    const n = pageNumber + by
    if (n >= 0 && n < pages.length) return openPage(n)
    const next = partBy(by)
    if (by > 0) return openPart(next.id, 0)
    pageOfLine(bookId, next.id).then(([, all]) => openPart(next.id, all.length - 1)).catch(() => {})
  }
  // A page turned by hand (the buttons under the page, a swipe) opens at its top: left
  // where it was, the reader landed at the end of the new page, below what they were turning to.
  useEffect(() => {
    if (!turned.current) return
    turned.current = false
    if (card.current?.getBoundingClientRect().top < 0) scrollToEl(card.current, 'top')
  }, [card, part, pageNumber])
  const atStart = pageNumber === 0 && !partBy(-1)
  const atEnd = pageNumber >= pages.length - 1 && !partBy(1)
  const swipe = useSwipe(!atStart && (() => stepPage(-1)), !atEnd && (() => stepPage(1)))
  // Where the page falls in the book, so a step either way slides in from its own side;
  // a link finding its page is no step, so it does not slide.
  const slide = useSlide((parts?.findIndex((p) => p.id === part) ?? 0) * 10000 + pageNumber, landing)
  return { partBy, stepPage, atStart, atEnd, swipe, slide }
}

/** Which words are missing, and the options offered for them. */
export function useGaps({ data, page, pageNumber, deal, difficulty, way, hidden, startFrom, pinned }) {

  // The gaps depend on the page, the difficulty and the deal; and on nothing
  // else, so typing an answer never moves them.
  const blanks = useMemo(
    () => {
      if (!page) return new Set()
      if (hidden) return fromMemory(page, startFrom, pinned == null)
      return blanksFor(page, difficultyOf(difficulty).share, makeRandom(pageNumber * 131 + deal))
    },
    [page, hidden, startFrom, pinned, difficulty, pageNumber, deal],
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
  return { blanks, choices }
}

/**
 * Each page opened is a step the back arrow returns to; a step returned to,
 * or handed over from another tab, opens its page here.
 * The page landed on is that step already, even when the step named a later
 * line on it ("2:255" opens the page from 2:250): recording it again would
 * push a new step and trap the back arrow there.
 * `landing` is true from a link's first render until its page is found (the part's first page is
 * not it), so the panel shows nothing of the book in between rather than a page that then jumps.
 */
export function useArrivedPage({ arrival, incoming, onVisit, bookId, part, page, pageOfLine, openBook, openPart }) {
  const arriving = useRef(false)
  const landed = useRef(null)
  const inPart = useRef(null)
  const [landing, setLanding] = useState(() => linkOf(incoming) !== null)
  useArrivalEffect(arrival, () => {
    const link = linkOf(incoming)
    if (!link) return setLanding(false)
    arriving.current = true
    pageOfLine(link.book, link.part, link.line).then(([n, all]) => {
      const at = Math.max(n, 0)
      landed.current = placeOf(link.book, link.part, all[at][0])
      if (link.book !== bookId) openBook(link.book)
      openPart(link.part, at)
    }).catch(() => {}).finally(() => { arriving.current = false; setLanding(false) })
  })
  const here = page && placeOf(bookId, part, page[0])
  useEffect(() => {
    if (!here || arriving.current) return
    // Another page of the part already open takes its step's place; a new part or book is a step.
    const over = inPart.current === `${bookId}/${part}`
    inPart.current = `${bookId}/${part}`
    if (here === landed.current) return
    landed.current = null
    onVisit?.(here, over)
  }, [here])  // eslint-disable-line react-hooks/exhaustive-deps
  return landing
}
