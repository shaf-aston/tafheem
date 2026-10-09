/**
 * Memorise, a page of a book with words taken out, for you to put back.
 *
 * The reader picks a book, a part of it, how much to take out, and whether to
 * type each missing word or choose it from a short list; the page is then
 * shown as it is printed, with a gap where each missing word was. Nothing is
 * marked until the whole page is checked at once, because stopping to be told
 * after every word turns recitation into a series of separate questions.
 *
 * The rules for what a page is and which words go are in lib/memorise.js, with
 * no knowledge of the screen; the books are in lib/books.js, with no knowledge
 * of either. This file only shows what those two decide.
 */
import { Fragment, useEffect, useMemo, useRef, useState } from 'react'
import { useQueries, useQuery, useQueryClient } from '@tanstack/react-query'

import { getSimilar, getSimilarSurah } from '../api'
import { isQuranic, recitedForm } from '../lib/arabicText'
import { BOOKS, bookPartQuery, bookPartsQuery, DEFAULT_BOOK } from '../lib/books'
import {
  blanksFor, CHOICES, DEFAULT_DIFFICULTY, DIFFICULTIES, fromMemory, isRight, makeRandom,
  optionsFor, pagesOf, printedPageOf, score, wordsOf,
} from '../lib/memorise'

import { closestSpans, flagsOnPage, twinKeys } from '../lib/similar'
import { readViewParam, writeViewParams } from '../lib/tabUrl'
import { useSlide, useSwipe } from '../lib/useSwipe'
import { scrollToEl } from '../lib/scrollToEl'
import { useReciting } from '../lib/useReciting'
import { useSetting } from '../lib/settings'
import { warm } from '../lib/warm'
import { useArrivalEffect } from '../lib/useArrival'
import recite from '../recite.json'

import { LOOK, SHOWN } from '../lib/reciteColors'

import ArabicText from './ui/ArabicText'
import AyahNumber from './ui/AyahNumber'
import ReciteStrip from './ReciteStrip'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import PrimaryButton from './ui/PrimaryButton'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import TwinCards from './ui/TwinCard'
import WheelPicker from './ui/WheelPicker'
import { Skeleton } from './ui/Skeleton'

// The setting itself, not a copy of one of its numbers. Every id here comes
// from DIFFICULTIES, so a miss means memorise.json names a default that is not
// in its own list, and that should stop the page rather than quietly deal a
// share nobody chose.
const difficultyOf = (id) => DIFFICULTIES.find((d) => d.id === id)

// What "Hidden" means while reciting. The same setting the page opens on, so
// choosing it and choosing it in typing mode leave the page in one state.
const HIDDEN = DEFAULT_DIFFICULTY

// A line's label carries the part it is in, so "3:158" repeats a surah the
// control beside it already names. Inside that surah the number alone says it.
// A book whose lines are not numbered this way is left exactly as it is.
const withinPart = (label) => label.split(':').pop()

// How long a finished page stays up, marked, before the next one turns in.
const TURN_AFTER_MS = recite['turn-after-s'] * 1000

// A page as a step on the back arrow's path: its first line, "2:6", with the
// book in front when it is not the Qur'an, "jazariyya/3:12".
const PLACE = /^(?:([a-z]+)\/)?(\d+):(\d+)$/
const placeOf = (bookId, part, line) => `${bookId === DEFAULT_BOOK ? '' : `${bookId}/`}${part}:${line.id}`

// Two ways to answer the same gap. Typing is recall; choosing is recognition,
// which is easier, and the only one that works without an Arabic keyboard.
const WAYS = [
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

export default function MemorisePanel({ accent, incoming, arrival, onVisit }) {
  const [bookId, setBookId] = useState(DEFAULT_BOOK)
  // What the reader picked, which is nothing until they pick; the part
  // actually open is derived below, once the book has said what its parts are.
  const [chosen, setChosen] = useState(null)
  const [pageNumber, setPageNumber] = useState(0)
  const [difficulty, setDifficulty] = useState(DEFAULT_DIFFICULTY)
  // Bumped to deal a fresh set of gaps over the same page.
  const [deal, setDeal] = useState(1)
  const [answers, setAnswers] = useState({})
  const [checked, setChecked] = useState(false)
  const [meaning, setMeaning] = useState(BOOKS[DEFAULT_BOOK].meaningDefault ?? false)
  // In the address as mode=, so a link (the landing page's "Recite, be heard")
  // can open the page already reciting.
  const [way, setWay] = useState(() => readViewParam('mode', WAYS.map((w) => w.id)) ?? 'type')
  useEffect(() => { writeViewParams({ mode: way === 'type' ? '' : way }) }, [way])
  const similar = way === 'similar'
  // The word the reader pressed to start on, or null for "they did not say".
  // A page is not always begun at its top: somebody revising picks up where
  // they stopped, or goes back over the one ayah they keep losing. It is
  // pressed on the word itself, so there is no control to find; and when it is
  // not pressed at all, the recitation says where it began and the page
  // follows that instead. Pressing always wins, because a reader who has said
  // where they are is not to be argued with by a microphone.
  const [pinned, setPinned] = useState(null)
  // Words uncovered by asking rather than by saying them. Kept apart from the
  // marks for exactly that reason: being shown a word is not reciting it.
  const [shown, setShown] = useState(() => new Set())
  // Whether recording again carries on the same recitation or begins the page
  // afresh. The reader's own choice, in the settings panel, because both are
  // reasonable: one person paused to look a word up, another gave up.
  const resume = useSetting('resume-reciting')

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
  // The mushaf page this one actually is, when the layout has been built. Null
  // means the pages were sized by word count, and saying "page 3 of 21" without
  // claiming a printed number is the honest thing to show for that.
  const printedPage = printedPageOf(page)

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

  // Reciting from memory covers the page rather than sampling it, so which
  // words are missing is a different question there and not a harder setting
  // of the same one; lib/memorise.js says why. The word to start on is only
  // ever a word of this page, so a shorter page cannot leave it pointing off
  // the end.
  const hidden = way === 'recite' && difficulty !== 'none'

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

  // Which ayahs of this surah have a twin, and the twins of the ones on this
  // page. Asked only in this mode, and only for ayahs that have one.
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

  // Anything that changes which words are missing starts the attempt over.
  // Done here, where the reader asks for the change, rather than by watching
  // the gaps afterwards, a watcher would also fire on the first render and
  // clear a page nobody had touched yet.
  const fresh = () => {
    setAnswers({})
    setChecked(false)
    setShown(new Set())
  }
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
  const chooseDifficulty = (id) => { setDifficulty(id); fresh() }
  const reDeal = () => { setDeal((n) => n + 1); fresh() }
  const chooseWay = (id) => { setWay(id); fresh() }

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

  const marks = page ? score(page, blanks, answers) : { right: 0, total: 0 }


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
  // The part `by` either side of this one: past a surah's last page is the next
  // surah, before its first is the one before.
  const partBy = (by) => parts?.[parts.findIndex((p) => p.id === part) + by]
  const turnPage = () => {
    if (pageNumber + 1 < pages.length) return carryOnAt(part, pageNumber + 1)
    if (partBy(1)) carryOnAt(partBy(1).id, 0)
  }
  // The pages of a part, fetched (or cached), and which holds a line (-1 for none).
  const pageOfLine = (b, partId, lineId) => client.fetchQuery(bookPartQuery(b, partId)).then(({ lines }) => {
    const all = pagesOf(lines, BOOKS[b].wordsPerPage)
    return [all.findIndex((p) => p.some((line) => line.id === lineId)), all]
  })
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

  // Each page opened is a step the back arrow returns to; a step returned to,
  // or handed over from another tab, opens its page here.
  // The page landed on is that step already, even when the step named a later
  // line on it ("2:255" opens the page from 2:250): recording it again would
  // push a new step and trap the back arrow there.
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
  const [stayed, setStayed] = useState(null)
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

  // Above the page and again under it, so a page read to its end turns from there.
  const pageSteps = (
    <span className="flex items-center gap-2">
      <StepButton onClick={() => stepPage(-1)} disabled={atStart}>Previous</StepButton>
      <StepButton onClick={() => stepPage(1)} disabled={atEnd}>Next</StepButton>
    </span>
  )

  return (
    <div className="panel" {...swipe}>
      <SectionHeader
        title="Memorise"
        arabic="حفظ"
        subtitle="Fill in the gaps"
      />

      {/* One row, no captions: each control's choices already say what it is,
          and the captions were a second row of grey restating them. Their
          words stay as screen-reader labels and hover titles. */}
      <div className="flex flex-wrap items-center gap-2">
        <WheelPicker
          label="Book"
          options={Object.values(BOOKS)}
          value={bookId}
          onChange={openBook}
          accent={accent}
        />

        <WheelPicker
          label={book.partLabel}
          options={parts ?? []}
          value={part}
          onChange={openPart}
          accent={accent}
          className="max-w-[18rem]"
        />

        <Segmented
          label="How you answer"
          options={WAYS.filter((w) => !w.onlyIf || w.onlyIf(book))}
          value={way}
          onChange={chooseWay}
          accent={accent}
        />

        {/* Reciting has two states worth choosing between, not five: the page
            read from, or the page said from memory. */}
        {!similar && <div title={way === 'recite' ? undefined : difficultyOf(difficulty).title}>
          <Segmented
            label={way === 'recite' ? 'Words to say from memory' : 'How much is missing'}
            options={way === 'recite'
              ? [{ id: 'none', label: 'Show all' }, { id: HIDDEN, label: 'Hidden' }]
              : DIFFICULTIES.map((d) => ({ id: d.id, label: d.label }))}
            value={way === 'recite' && difficulty !== 'none' ? HIDDEN : difficulty}
            onChange={chooseDifficulty}
            accent={accent}
          />
        </div>}
      </div>

      {isPending && <Skeleton className="h-40 w-full" />}

      {isError && (
        <ErrorAlert title="That part could not be read" error={error} fallback="The text comes from the Qur\'an tab\'s own source." onRetry={refetch} />
      )}

      {data && pages.length === 0 && <EmptyState>Nothing to memorise here.</EmptyState>}

      {page && (
        <>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="text-sm text-[var(--text-dim)] flex items-center gap-2 flex-wrap">
              {/* A picker, not steps alone: stepping is fine for the next page
                  and useless for the fifteenth. The mushaf page, when known,
                  is the number a memoriser already uses, so it is the label. */}
              {/* Valued by the number it shows, so typing "177" finds Mushaf p.177. */}
              <span title={printedPage != null ? 'Page in the 604-page Madani mushaf' : undefined}>
                <WheelPicker
                  label="Page"
                  options={pages.map((p, n) => ({
                    id: printedPageOf(p) ?? n + 1,
                    label: `${printedPageOf(p) != null ? `Mushaf p.${printedPageOf(p)}` : `Page ${n + 1} of ${pages.length}`} · ${withinPart(p[0].label)}–${withinPart(p[p.length - 1].label)}`,
                  }))}
                  value={printedPage ?? pageNumber + 1}
                  onChange={(no) => openPage(pages.findIndex((p, n) => (printedPageOf(p) ?? n + 1) === no))}
                  accent={accent}
                />
              </span>
              {pageSteps}
              {/* One short live line: where reciting is following from, or the
                  one thing worth knowing before typing. Where to begin is
                  chosen on the page itself, a word at a time. */}
              <span className="text-[var(--text-faint)]" aria-live="polite">
                {way === 'recite'
                  ? reciting.marks.began != null
                    ? `following you from ${startLabel}`
                    : reciting.listening
                      ? 'listening for where you are'
                      : 'tap a word to start'
                  : way === 'type' || similar ? 'vowels not needed' : null}
              </span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {/* Only when there is something covered to uncover. Two sizes
                  of help, because being stuck on one word and having lost the
                  thread of a whole ayah are not the same trouble. What they
                  give is marked as given, never as recited. */}
              {hidden && way === 'recite' ? (
                <>
                  <StepButton onClick={() => show(false)}>Show a word</StepButton>
                  <StepButton onClick={() => show(true)}>Show this ayah</StepButton>
                </>
              ) : !similar && (
                <StepButton onClick={reDeal}>New gaps</StepButton>
              )}
              {/* Off to start with, and that is the point: "Say He (is) Allah
                  the One" names both words missing from 112:1. It is here for
                  when you are stuck, not for while you are trying. */}
              <StepButton onClick={() => setMeaning((on) => !on)}>
                {meaning ? 'Hide translation' : 'Show translation'}
              </StepButton>
            </div>
          </div>

          {/* Mounted always, so a screen reader hears the question when it
              appears; empty, it takes no room. */}
          <div role="status" className="empty:absolute">
            {askToGo && (
              <div className="flex items-center gap-3 flex-wrap">
                <span className="type-small text-[var(--text-dim)]">You seem to be reciting {where}.</span>
                <StepButton onClick={goElsewhere}>Go there</StepButton>
                <StepButton onClick={() => setStayed(elsewhere.surah)}>Stay</StepButton>
              </div>
            )}
          </div>

          <div ref={card} key={`${bookId}/${part}/${pageNumber}`} {...slide}
            className={`rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-4 scroll-mt-4 ${slide.className}`}>
            {/* A flowing book runs its lines on as a printed mushaf does: one
                block, justified, each ayah ending in its number, and never a
                new row per ayah, which left short ayahs a gutter of empty space.
                The last row's leftover space goes to the ::after filler, so
                only that row sits to the start instead of being stretched. On a
                phone a row holds two or three words, and stretching those left
                holes wider than the words, so there it simply packs. */}
            <div
              className={book.flow
                ? "flex flex-wrap items-baseline gap-x-2 gap-y-2 sm:justify-between after:content-[''] after:flex-1"
                : 'space-y-4'}
              dir="rtl"
            >
              {page.map((line, l) => (
                <Line
                  key={line.id}
                  flow={book.flow}
                  line={line}
                  index={l}
                  blanks={blanks}
                  answers={answers}
                  checked={checked}
                  meaning={meaning}
                  choices={choices}
                  accent={accent}
                  twin={similar && twinned.has(line.label)}
                  recite={way === 'recite'
                    ? { ...reciting.marks, from: recitedPage.lines[l].from, shown }
                    : null}
                  // Pressable while listening too: jumping back or ahead must not
                  // mean stopping first. forget() keeps the microphone running.
                  onStartAt={way === 'recite' ? openAt : null}
                  onAnswer={(key, value) => setAnswers((was) => ({ ...was, [key]: value }))}
                />
              ))}
            </div>
            {/* Run on, a line has nowhere under it for its English, so the
                page's translation follows the Arabic, one ayah to a line. */}
            {book.flow && meaning && (
              <ol className="space-y-2">
                {page.filter((line) => line.english).map((line) => (
                  <li key={line.id} className="type-body text-[var(--text-dim)] leading-relaxed max-w-prose">
                    <span className="type-small text-[var(--text-faint)] tabular-nums" aria-hidden="true">{withinPart(line.label)}. </span>
                    {line.english}
                  </li>
                ))}
              </ol>
            )}
          </div>

          {way === 'recite' ? (
            <ReciteStrip
              listening={reciting.listening}
              problem={reciting.problem}
              heard={reciting.heard}
              marks={reciting.marks}
              lines={recitedPage.lines}
              accent={accent}
              onStart={listen}
              onStop={reciting.stop}
            />
          ) : blanks.size === 0 ? (
            // Two different reasons land here: the reader chose "None" to just
            // read the page, or every line on it is one word long so there was
            // nothing to take out even at a harder setting. Only the second is
            // worth saying, the first is exactly what was asked for.
            !similar && difficulty !== 'none' && (
              <EmptyState>
                Every line here is one word long, so there is nothing to take out.
              </EmptyState>
            )
          ) : (
            <div className="space-y-2">
              {/* One button, two jobs: mark the page, then clear it for another
                  go at the same gaps. "New gaps" is the other button because it
                  moves them, and after being shown the answers you want the
                  same ones back, not a different page. */}
              <PrimaryButton
                accent={accent}
                onClick={checked ? fresh : () => setChecked(true)}
              >
                {checked ? 'Try this page again' : 'Check this page'}
              </PrimaryButton>
              {/* Said only once the page has been marked. A running count while
                  typing would be answering each gap as it is filled, which is
                  the thing this panel is built not to do. */}
              {checked && (
                <p className="text-sm text-center text-[var(--text-dim)]" aria-live="polite">
                  {marks.right} of {marks.total} right
                  {marks.right < marks.total && ', the missed words are shown above'}
                </p>
              )}
            </div>
          )}
          {similar && (
            <SimilarCards
              lines={twinLines}
              queries={twinQueries}
              surah={twinsOfSurah}
              accent={accent}
            />
          )}
          <div className="flex justify-center">{pageSteps}</div>
        </>
      )}
    </div>
  )
}

/** The twin cards under the page: the surah's groups first, then one set per twinned ayah. */
function SimilarCards({ lines, queries, surah, accent }) {
  if (surah.isPending || surah.isError) return <TwinCards mine={null} query={surah} accent={accent} />
  if (lines.length === 0) return <EmptyState>No similar verses recorded on this page.</EmptyState>
  return (
    <div className="space-y-4">
      {lines.map(({ line }, i) => (
        <TwinCards key={line.label} mine={{ key: line.label, text: line.arabic }} query={queries[i]} accent={accent} />
      ))}
    </div>
  )
}

function StepButton({ onClick, disabled, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="px-3 py-1.5 rounded-full text-xs font-medium border border-[var(--border)]
        text-[var(--text-dim)] hover:text-[var(--text)] disabled:opacity-40
        disabled:hover:text-[var(--text-dim)] transition-colors"
    >
      {children}
    </button>
  )
}

/**
 * One line of the book, right to left, with a box where each missing word was.
 *
 * The English sits under it throughout. It is a translation of the whole line,
 * never of the missing word on its own, so it is a reminder of where you are
 * rather than the answer.
 */
function Line({ line, flow, index, blanks, answers, checked, meaning, choices, accent, twin, recite, onStartAt, onAnswer }) {
  const words = wordsOf(line.arabic)
  // One width for every typed blank on this line, from the longest recited
  // word among them: sizing each blank to its own answer leaks the length.
  const typeWidth = Math.max(
    3,
    ...words
      .map((word, w) => (blanks.has(`${index}:${w}`) ? recitedForm(word).length : 0)),
  ) + 1
  const drawn = words.map((word, w) => {
    const key = `${index}:${w}`
    // A poem's bayt is two hemistichs, sadr then ajuz, printed as one
    // line but never run together, forcing a wrap here after the sadr
    // shows that split without needing a second Line per bayt, which
    // would let pagesOf and the blank-picker split them across a page.
    const hemistichBreak = line.breakAfter === w && (
      <span key={`${key}:break`} className="basis-full h-0" aria-hidden="true" />
    )
    if (!blanks.has(key)) {
      return (
        <Fragment key={key}>
          {/* The display size, as the Qur'an tab and the surah reader set the
              text being read; the reading size made the mushaf look smaller. */}
          {recite
            ? <RecitedWord word={word} at={recite.from + w} recite={recite} accent={accent} onStartAt={onStartAt} />
            : <ArabicText size="lg">{word}</ArabicText>}
          {hemistichBreak}
        </Fragment>
      )
    }
    // Reciting a page you can read is not a test of remembering it. So
    // the same words that would be gaps to type stay covered here, and
    // the only thing that uncovers one is saying it.
    if (recite) {
      return (
        <Fragment key={key}>
          <RecitedWord
            word={word}
            at={recite.from + w}
            recite={recite}
            accent={accent}
            coverWidth={typeWidth}
            onStartAt={onStartAt}
          />
          {hemistichBreak}
        </Fragment>
      )
    }
    return (
      <Fragment key={key}>
        <Gap
          word={word}
          options={choices?.get(key)}
          value={answers[key] ?? ''}
          checked={checked}
          accent={accent}
          lineLabel={line.label}
          typeWidth={typeWidth}
          onChange={(value) => onAnswer(key, value)}
        />
        {hemistichBreak}
      </Fragment>
    )
  })
  const number = flow
    ? <AyahNumber aria-label={`ayah ${withinPart(line.label)}`}>{withinPart(line.label)}</AyahNumber>
    : <AyahNumber>{line.label}</AyahNumber>
  const marker = twin ? (
    <>
      {number}
      <span
        role="img"
        aria-label="has similar verses"
        title="has similar verses"
        className="w-1.5 h-1.5 rounded-full shrink-0 bg-[var(--text-faint)]"
      />
    </>
  ) : number
  // Flowing, the line's two boxes step aside (display: contents) so its words
  // join the page's one run; the words themselves are drawn the same either way.
  return (
    <div className={flow ? 'contents' : 'space-y-1'}>
      {/* Right to left, wrapping downward, exactly as the line is printed. The
          reference goes last so it sits at the end of the line the way a mushaf
          puts the ayah number, in a right-to-left row, last is leftmost. */}
      <div
        className={flow ? 'contents' : 'flex flex-wrap items-baseline gap-x-2 gap-y-1'}
        dir="rtl"
        data-script={isQuranic(line.arabic) ? 'quran' : undefined}
      >
        {flow ? (
          <>
            {drawn.slice(0, -1)}
            {/* The last word and the ayah's number wrap as one, so a number
                is never left alone at the start of a row. */}
            <span className="inline-flex items-baseline gap-x-2">
              {drawn.at(-1)}
              {marker}
            </span>
          </>
        ) : (
          <>
            {drawn}
            {marker}
          </>
        )}
      </div>
      {/* The body size, not a label size: this is the translation being read,
          and it is the same text the surah reader one tab away already sets at
          this size. */}
      {!flow && meaning && line.english && (
        <p className="type-body text-[var(--text-dim)] leading-relaxed max-w-prose">
          {line.english}
        </p>
      )}
    </div>
  )
}

/**
 * One word of the page while it is being recited.
 *
 * Four things can be true of it, and each looks different because each means
 * something different: not reached yet, said and right, said and not sure, said
 * and wrong. A word never said at all is outlined rather than coloured in,
 * because there is nothing there to colour.
 *
 * What came back sits beside the word on the same line, never under it: under
 * it is where it was first put and it was too hard to see.
 */
function RecitedWord({ word, at, recite, accent, coverWidth, onStartAt }) {
  const mark = recite.words[at] ?? { state: 'waiting', heard: '' }
  // A word that was asked for rather than said. It is not one of the follower's
  // states, so it is read here and never written back into the marks.
  const wasShown = recite.shown?.has(at) && mark.state === 'waiting'
  const look = wasShown ? SHOWN : LOOK[mark.state]
  const missed = mark.state === 'missed'
  const here = at === recite.at
  const added = recite.extras.filter((extra) => extra.after === at)
  // A covered word shows nothing until it has been reached, right or wrong, or
  // asked for. Every cover on a line is the same width, taken from the longest
  // word among them, because a cover the size of its own word gives it away.
  const covered = coverWidth && mark.state === 'waiting' && !wasShown

  const printed = covered ? (
    <span
      aria-label="a word to say from memory"
      className="inline-block border-b align-baseline"
      style={{
        width: `${coverWidth}ch`,
        height: '1.2em',
        borderColor: here ? accent : 'var(--border)',
      }}
    />
  ) : (
    <ArabicText
      size="lg"
      title={wasShown ? SHOWN.label : look?.label}
      style={{
        color: look?.colour,
        // Where the reciter is, so the eye finds its place on a full page.
        boxShadow: here ? `0 2px 0 ${accent}` : undefined,
        // Dashed, so a word you were given never reads as a word you said,
        // even to somebody who cannot tell the two greys apart.
        ...(wasShown ? { borderBottom: '1px dashed var(--text-faint)' } : {}),
        ...(missed ? { border: '1px solid var(--danger)', borderRadius: '6px', padding: '0 4px' } : {}),
      }}
    >
      {word}
    </ArabicText>
  )

  return (
    <>
      {/* The page is the control: pressing a word starts the recitation there.
          A button rather than a click handler on the text, so it is reachable
          by keyboard and announces itself, and it carries no look of its own. */}
      {onStartAt ? (
        <button
          type="button"
          onClick={() => onStartAt(at)}
          title="start reciting from here"
          aria-label={`start reciting from ${word}`}
          className="inline-flex items-baseline bg-transparent p-0 cursor-pointer rounded-[var(--radius-sm)]
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--c)]/40"
        >
          {printed}
        </button>
      ) : printed}
      {mark.heard && (
        <ArabicText
          size="sm"
          title="what the microphone heard"
          style={{ color: look?.colour, borderColor: look?.colour }}
          className="border rounded-[var(--radius-sm)] px-1.5"
        >
          {`← ${mark.heard}`}
        </ArabicText>
      )}
      {added.map((extra) => (
        <ArabicText
          key={extra.heard}
          size="sm"
          title="said, and not in the book"
          style={{ color: 'var(--danger)', borderColor: 'var(--danger)' }}
          className="border border-dashed rounded-[var(--radius-sm)] px-1.5"
        >
          {extra.heard}
        </ArabicText>
      ))}
    </>
  )
}

/** One missing word: a box to type into, and after checking, how it went. */
function Gap({ word, options, value, checked, accent, lineLabel, typeWidth, onChange }) {
  const right = checked && isRight(value, word)
  const wrong = checked && !right
  const border = wrong ? 'var(--danger)' : right ? 'var(--success)' : 'var(--border)'
  const gapLabel = `missing word, ${lineLabel}`

  return (
    <span className="inline-flex flex-col items-center">
      {options ? (
        // The four words, on the app's one picker (ui/WheelPicker), drawn as a
        // blank in the line: a page can hold a dozen gaps, and four buttons
        // each would be a wall rather than a line of text to read. Every gap
        // is as wide as its own longest choice, so the row does not jump as
        // words are picked; sizing by the answer would give its length away.
        // Read-only after checking, so a marked answer keeps its focus ring.
        <span
          className="memorise-gap"
          style={{
            '--gap-border': border,
            '--gap-text': right || wrong ? border : undefined,
            width: `${Math.max(...options.map((o) => recitedForm(o).length)) + 5}ch`,
          }}
        >
          <WheelPicker
            label={gapLabel}
            placeholder="…"
            options={options.map((option) => ({ id: option, label: option }))}
            value={value}
            onChange={onChange}
            readOnly={checked}
            arabic
            accent={accent}
          />
        </span>
      ) : (
      <ArabicText
        as="input"
        size="lg"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        readOnly={checked}
        aria-label={gapLabel}
        style={{ '--gap-border': border, caretColor: accent, width: `${typeWidth}ch` }}
        className="bg-transparent border-b-2 text-center outline-none
          border-[color:var(--gap-border)] focus-visible:border-[color:var(--c)]
          focus-visible:ring-2 focus-visible:ring-[color:var(--c)]/40 focus-visible:outline-none
          transition-colors"
      />
      )}
      {/* The word itself, once the page is marked and only where it was missed.
          Showing it beside a right answer would just be printing it twice. */}
      {wrong && (
        <ArabicText size="sm" className="text-[var(--danger)]">{word}</ArabicText>
      )}
    </span>
  )
}
