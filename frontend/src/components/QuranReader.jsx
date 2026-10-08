/**
 * The Quran tab's one view: a whole surah, read, with the ayah being studied
 * beside it. Opening one ayah opens its surah scrolled to it, so the ayah is
 * always read in its place, and the study (AyahStudy) sits in a column to the
 * right, or under it on a screen too narrow for two columns: the surah above,
 * the study below, and a bar between them to drag either one bigger.
 *
 * One request brings the surah's text and its English, 35ms for al-Baqarah,
 * the longest. The word-by-word grammar is not fetched here: it is ~2MB for a
 * long surah and is only worth loading for the ayah being studied.
 *
 * The request was never the wait. Measured 2026-09-04: both answers were back
 * in 180ms and al-Baqarah appeared at 2,000ms, the rest spent drawing 286 rows
 * before the first could be shown. Two things fix that: the first screen of
 * rows is drawn first (AyahList), and rows off the screen are not laid out
 * (.surah-row).
 *
 * One reciter and one recitation for the whole view, held here: the bar plays
 * by them and every row lights its words by them, so the two cannot disagree
 * about which recording is sounding.
 */
import { useCallback, useDeferredValue, useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { getSurahGlosses, quranSurahQuery } from '../api'
import { warm } from '../lib/warm'
import { ayahEnd } from '../lib/ayahEnd'
import { useTranslation } from '../lib/useTranslation'
import { useRecitation } from '../lib/useRecitation'
import { useRecitedWord } from '../lib/useRecitedWord'
import { RECITERS, nowPlaying, play, prefetch, stop, watch, watchEnd } from '../lib/ayahAudio'
import { useRemembered, useRememberedFlag } from '../lib/useRemembered'
import { learntWords } from '../lib/coverage'
import { useLearntLemmas } from '../lib/useLearntLemmas'
import { useMedia } from '../lib/useMedia'
import { useWheelX } from '../lib/useWheelX'
import { scrollToEl } from '../lib/scrollToEl'
import { useSlide, useSwipe } from '../lib/useSwipe'

import AyahStudy from './AyahStudy'
import { NoTouchButton, ScrollPad } from './NoTouchReading'
import ArabicText from './ui/ArabicText'
import GlossWord from './ui/GlossWord'
import ReadingOptions from './ui/ReadingOptions'
import ErrorAlert from './ui/ErrorAlert'
import Segmented from './ui/Segmented'
import WheelPicker from './ui/WheelPicker'
import { Skeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'

// The reciters as the dropdown's choices, each with its Arabic name beside it.
const VOICES = RECITERS.map((one) => ({ id: one.id, label: one.name, hint: one.arabic }))

const FIRST_SURAH = 1
const LAST_SURAH = 114
// Rows drawn before the surah is shown; more than fill the list's first screen.
// The rest are drawn after it is on screen, in a render the browser may
// interrupt, so a long surah appears as fast as a short one.
const FIRST_PAINT_ROWS = 12
// Wide enough for the surah and the study side by side; Tailwind's lg.
const TWO_PANES = '(min-width: 64rem)'
const TOUCH = '(pointer: coarse)'

/** The English under one ayah: the chosen translation once it has arrived,
 *  the corpus's word-by-word gloss before that, so nothing is credited to a
 *  book it did not come from. */
const englishFor = (translation, ayah) => (translation.ready ? translation.textFor(ayah.ayah) : ayah.english)

/** The ayah whose row is at the top of the list, counting from 1. Rows are
 *  in ayah order, so a binary search over their offsets. */
function rowAt(list) {
  const rows = list.children
  let lo = 0
  let hi = rows.length - 1
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1
    if (rows[mid].offsetTop <= list.scrollTop + 8) lo = mid
    else hi = mid - 1
  }
  return lo + 1
}

/** Put an ayah's row at the top of the list, moving the list and not the page. */
function showRow(list, ayah) {
  const row = list?.children[ayah - 1]
  if (row) list.scrollTop = row.offsetTop
}

// What the reader does to take over the scrolling from the page.
const TAKE_OVER = ['pointerdown', 'wheel', 'touchstart', 'keydown']

export default function QuranReader({ place, accent, onGo, onPlace, onClose }) {
  const { surah, ayah } = place
  const twoPanes = useMedia(TWO_PANES)
  const [reciter, chooseReciter] = useRemembered('reciter', RECITERS.map((one) => one.id))

  const { data, isPending, isError, error, refetch } = useQuery(quranSurahQuery(surah))
  const client = useQueryClient()
  useEffect(() => {
    if (surah < LAST_SURAH) warm(client, quranSurahQuery(surah + 1))
  }, [client, surah])

  // The English of each word, for the hover gloss. Its own request so the text
  // is never held up by it, and reads normally for good if it never arrives.
  const { data: glosses } = useQuery({ queryKey: ['surah-glosses', surah], queryFn: () => getSurahGlosses(surah) })
  const learnt = useLearntLemmas()
  const [allMeanings, showAllMeanings] = useRememberedFlag('reader-all-meanings', false)
  const anyGlosses = Object.keys(glosses?.ayahs ?? {}).length > 0
  // Reading without touching the words: a switch in the bar, which the reader
  // may take out of the bar, and which is off whenever it is out of reach.
  const touch = useMedia(TOUCH)
  const [noTouchButton, showNoTouchButton] = useRememberedFlag('reader-no-touch-button', true)
  const [noTouchOn, setNoTouch] = useRememberedFlag('reader-no-touch', false)
  const noTouch = touch && noTouchButton && noTouchOn
  const recitation = useRecitation(surah, reciter)
  const translation = useTranslation(surah)

  const list = useRef(null)
  // The ayah at the top of the list as it is scrolled: the rail follows it.
  const [here, setHere] = useState(ayah ?? 1)
  // A row tapped is already in view; only an ayah opened from elsewhere is
  // scrolled to.
  const [tapped, setTapped] = useState(null)
  const [hereIn, setHereIn] = useState(surah)
  if (hereIn !== surah) { setHereIn(surah); setHere(ayah ?? 1); setTapped(null) }
  // Narrow, an ayah studied splits the reader in two, one over the other;
  // `share` is how much of it the surah keeps.
  const stacked = !twoPanes && Boolean(ayah)
  const panes = useRef(null)
  const [share, setShare] = useState(0.5)
  // Splitting brings the two panes up to fill the screen, the ayah at the top
  // of its half: the half it was in may end above it.
  const wasStacked = useRef(false)
  useEffect(() => {
    if (!stacked) wasStacked.current = false
    if (!stacked || !data || wasStacked.current) return
    wasStacked.current = true
    scrollToEl(panes.current, 'top')
    showRow(list.current, ayah)
  }, [stacked, ayah, data])
  const goTo = useCallback((n) => { showRow(list.current, n); setHere(n) }, [])
  const open = (n) => { setTapped(n); onPlace({ surah, ayah: n }) }
  // Focus goes back to the ayah's row, not lost with the close button.
  const shut = useCallback(() => {
    onPlace({ surah, ayah: null })
    list.current?.children[ayah - 1]?.querySelector('button')?.focus({ preventScroll: true })
  }, [onPlace, surah, ayah])
  const changeSurah = useCallback((n) => onPlace({ surah: n, ayah: null }), [onPlace])

  // ← → change surah and Esc shuts the study, then the reader. Not while typing,
  // and not while a sheet is open: it handles its own Esc.
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return
      // Arrows belong to whatever has its own: a field, a strip, a row of choices.
      if (e.target.closest('input, textarea, select, .strip-x, [role="group"]') || document.querySelector('dialog[open]')) return
      if (e.key === 'ArrowLeft' && surah > FIRST_SURAH) changeSurah(surah - 1)
      if (e.key === 'ArrowRight' && surah < LAST_SURAH) changeSurah(surah + 1)
      if (e.key === 'Escape') (ayah ? shut : onClose)()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [surah, ayah, changeSurah, shut, onClose])
  const swipe = useSwipe(surah > FIRST_SURAH && (() => changeSurah(surah - 1)),
    surah < LAST_SURAH && (() => changeSurah(surah + 1)))
  const slide = useSlide(surah)

  const study = ayah && (
    <AyahStudy key={`${surah}:${ayah}`} surah={surah} ayah={ayah} onGo={onGo} onClose={shut} accent={accent} />
  )

  return (
    <div {...swipe} style={{ '--c': accent }} className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] overflow-clip">
      <header className="flex items-center gap-3 flex-wrap p-4 border-b border-[var(--border)]">
        <Stepper surah={surah} onChange={changeSurah} />
        {data ? (
          <ArabicText size="sm" className="text-[var(--c)]">{data.name_ar}</ArabicText>
        ) : (
          <Skeleton className="h-4 w-24" />
        )}
        {data && <span className="type-small text-[var(--text-faint)] tabular-nums">{data.ayah_count} ayahs</span>}
        <span className="flex-1" />
        {/* Only where there is a choice to make. */}
        {translation.books.length > 1 && (
          <Segmented
            label="Translation"
            options={translation.books.map((book) => ({ id: book.id, label: book.short }))}
            value={translation.chosen}
            onChange={translation.choose}
            accent={accent}
            className="flex-wrap"
          />
        )}
        {/* The Arabic is the corpus's; the English may not be. Both are named. */}
        {translation.ready && translation.book?.source && <SourceBadge source={translation.book.source} />}
        {data?.source && <SourceBadge source={data.source} />}
        {touch && noTouchButton && <NoTouchButton on={noTouchOn} onChange={setNoTouch} />}
        <ReadingOptions accent={accent} options={[
          ...(anyGlosses ? [{ label: 'Every word\'s meaning', on: allMeanings, set: showAllMeanings }] : []),
          { label: 'Without-wudu button', on: noTouchButton, set: showNoTouchButton, only: 'touch' },
        ]} />
        <button
          type="button"
          onClick={onClose}
          className="text-xs text-[var(--text-faint)] hover:text-[var(--text)] transition-colors px-2 py-1"
        >
          Close
        </button>
      </header>

      {data && <AyahRail key={surah} count={data.ayah_count} here={here} open={ayah} onPick={goTo} />}

      <div key={surah} ref={panes} {...slide}
        className={twoPanes ? 'grid grid-cols-[minmax(0,1fr)_minmax(19rem,26rem)]' : stacked ? 'flex flex-col h-[var(--layout-split)] scroll-mt-14' : ''}>
        <div className={stacked ? 'min-w-0 min-h-0 shrink-0' : 'min-w-0'} style={stacked ? { height: `${share * 100}%` } : undefined}>
          {translation.isError && (
            <div className="p-4" aria-live="assertive">
              <ErrorAlert title="The translation could not be read" error={translation.error} fallback="The Arabic and its word-by-word English are unaffected." onRetry={() => translation.refetch()} />
            </div>
          )}
          {isError && (
            <div className="p-4" aria-live="assertive">
              <ErrorAlert title="Could not open that surah" error={error} fallback="The surah could not be loaded." onRetry={() => refetch()} />
            </div>
          )}
          {isPending && (
            <div className="p-4 space-y-3">
              {Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          )}
          {data && (
            <div className={`flex ${stacked ? 'h-full' : 'h-[var(--layout-pane)]'}`}>
              <AyahList listRef={list} ayahs={data.ayahs} target={ayah === tapped ? null : ayah} still={noTouch} onScrolled={setHere}>
                {(row) => (
                  <AyahRow
                    key={row.ayah}
                    ayah={row}
                    english={englishFor(translation, row)}
                    glosses={glosses?.ayahs?.[row.ayah]}
                    learnt={learntWords(glosses?.lemmas?.[row.ayah], learnt)}
                    allMeanings={allMeanings}
                    src={recitation.urlFor(row.ayah)}
                    segments={recitation.segmentsFor(row.ayah)}
                    open={row.ayah === ayah}
                    onOpen={open}
                  />
                )}
              </AyahList>
              {touch && <ScrollPad list={list} on={noTouch} />}
            </div>
          )}
        </div>
        {twoPanes && (
          <aside aria-label="Study" className="scroll-pane h-[var(--layout-pane)] p-4 border-l border-[var(--border)]">
            {study || (
              <p className="type-small text-[var(--text-faint)]">
                Tap an ayah to study it here: every word's grammar and root, how the words join, and its tafsir.
              </p>
            )}
          </aside>
        )}
        {stacked && (
          <>
            <SplitBar panes={panes} share={share} onShare={setShare} />
            <aside aria-label="Study" className="scroll-pane flex-1 min-h-0 p-4">{study}</aside>
          </>
        )}
      </div>

      {data && (
        <RecitationBar
          key={surah}
          surah={surah}
          count={data.ayah_count}
          from={ayah ?? here}
          here={here}
          recitation={recitation}
          reciter={reciter}
          onReciter={(id) => { stop(); chooseReciter(id) }}
          onFollow={goTo}
        />
      )}
    </div>
  )
}

/**
 * One ayah, with each word's English shown while the pointer rests on it.
 *
 * Arabic joins its letters inside a word and never across a space, so drawing
 * every word in its own box changes nothing about the writing. `english`
 * missing means the two sources disagreed about how many words this ayah has;
 * the ayah is then drawn plain, and a gloss is never guessed onto a word.
 */
function GlossedAyah({ arabic, english, learnt, allMeanings, lit = -1, end }) {
  const line = 'block text-right leading-loose text-[var(--text)]'
  const mark = <span className="text-[var(--c)]" aria-hidden="true"> {end}</span>
  if (!english && !learnt && lit < 0) {
    return <ArabicText size="lg" className={line}>{arabic}{mark}</ArabicText>
  }
  return (
    <ArabicText size="lg" className={`${line} gloss-line${allMeanings ? ' gloss-all' : ''}`}>
      {arabic.split(' ').map((word, i) => (
        <span key={i}>
          {i > 0 && ' '}
          <GlossWord gloss={english?.[i]} lit={i === lit} learnt={learnt?.[i]}>{word}</GlossWord>
        </span>
      ))}
      {mark}
    </ArabicText>
  )
}

/**
 * One ayah of the surah: its line, closed by its numbered medallion, and its
 * English the full width under it. A row of its own because it asks which of
 * its words is being recited; all but the one sounding answer with a single
 * comparison.
 */
function AyahRow({ ayah, english, glosses, learnt, allMeanings, src, segments, open, onOpen }) {
  const lit = useRecitedWord(src, segments)
  return (
    <li className="surah-row">
      <button
        type="button"
        onClick={() => onOpen(ayah.ayah)}
        aria-pressed={open}
        className={`w-full text-left p-4 space-y-2 transition-colors hover:bg-[var(--surface-hi)]
          focus:outline-none focus-visible:bg-[var(--surface-hi)]
          ${open ? 'bg-[color-mix(in_srgb,var(--c)_8%,transparent)] shadow-[inset_0_0_0_1px_color-mix(in_srgb,var(--c)_35%,transparent)]' : ''}`}
      >
        <GlossedAyah arabic={ayah.arabic} english={glosses} learnt={learnt} allMeanings={allMeanings} lit={lit} end={ayahEnd(ayah.ayah)} />
        {english && (
          <span className="block type-body text-[var(--text)] leading-relaxed border-t border-[var(--border)] pt-2">
            {english}
          </span>
        )}
      </button>
    </li>
  )
}

/**
 * The rows of one surah, in a pane that scrolls on its own. A new surah is a
 * new list (the reader keys it), so it starts with only the first screen of
 * rows drawn, the rest following once those are on screen. `target` is the
 * ayah to open at: it may be past the first screen, so it is scrolled to once
 * its row exists. Rows off the screen are laid out at a guessed height
 * (.surah-row) and the Quran face arrives late, so the row moves as the rows
 * around it take their real size: it is held in place through every such
 * change until the reader scrolls or taps for themselves. `still` is reading
 * without touching the words: a finger on them scrolls, opens and shows nothing.
 */
function AyahList({ listRef, ayahs, target, still, onScrolled, children: row }) {
  const rows = useDeferredValue(ayahs, ayahs.slice(0, FIRST_PAINT_ROWS))
  const reached = target && rows.length >= target
  useLayoutEffect(() => {
    const list = listRef.current
    if (!reached || !list) return undefined
    const aim = () => showRow(list, target)
    aim()
    const sizes = new ResizeObserver(aim)
    for (const one of list.children) sizes.observe(one)
    const release = () => {
      sizes.disconnect()
      TAKE_OVER.forEach((type) => document.removeEventListener(type, release, true))
    }
    TAKE_OVER.forEach((type) => document.addEventListener(type, release, { capture: true, passive: true }))
    return release
  }, [listRef, reached, target])

  return (
    <ol
      ref={listRef}
      onScroll={(e) => onScrolled(rowAt(e.currentTarget))}
      className={`scroll-pane flex-1 min-w-0 h-full divide-y divide-[var(--border)] ${still ? 'touch-none [&>li]:pointer-events-none' : ''}`}
    >
      {rows.map(row)}
    </ol>
  )
}

// The least either pane keeps of the split, so neither can be dragged shut.
const LEAST = 0.2
const clampShare = (n) => Math.min(1 - LEAST, Math.max(LEAST, n))

/**
 * The bar between the surah and the study on a phone: drag it, or press the
 * arrows on it, to give one more room and the other less.
 */
function SplitBar({ panes, share, onShare }) {
  const drag = (e) => {
    if (!e.currentTarget.hasPointerCapture(e.pointerId)) return
    const box = panes.current.getBoundingClientRect()
    onShare(clampShare((e.clientY - box.top) / box.height))
  }
  const step = { ArrowUp: -0.1, ArrowDown: 0.1 }
  return (
    <div
      role="separator"
      aria-orientation="horizontal"
      aria-label="Resize the surah and the study"
      aria-valuenow={Math.round(share * 100)}
      aria-valuemin={LEAST * 100}
      aria-valuemax={(1 - LEAST) * 100}
      tabIndex={0}
      onPointerDown={(e) => e.currentTarget.setPointerCapture(e.pointerId)}
      onPointerMove={drag}
      onKeyDown={(e) => step[e.key] && (e.preventDefault(), onShare(clampShare(share + step[e.key])))}
      className="touch-none select-none shrink-0 grid place-items-center h-6 cursor-row-resize
        border-y border-[var(--border)] bg-[var(--surface-hi)] focus:outline-none focus-visible:bg-[var(--surface)]"
    >
      <span aria-hidden="true" className="w-10 h-1 rounded-full bg-[var(--border-hi)]" />
    </div>
  )
}

/**
 * Every ayah's number in one sideways strip, to jump straight to one. It
 * follows the reading: the ayah at the top of the list is marked and kept in
 * view, and the one being studied wears the accent. One stop for Tab, the
 * arrows walk it, so a long surah is not 286 presses to get past.
 */
function AyahRail({ count, here, open, onPick }) {
  const rail = useWheelX()
  useEffect(() => {
    const strip = rail.current
    const chip = strip?.children[here - 1]
    if (chip) strip.scrollTo({ left: chip.offsetLeft - (strip.clientWidth - chip.offsetWidth) / 2 })
  }, [rail, here])
  // Right is the next number, as the strip reads left to right.
  const walk = (e) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key]
    const n = Number(e.target.textContent) + (step ?? 0)
    if (step && n >= 1 && n <= count) rail.current.children[n - 1].focus()
  }

  return (
    <nav aria-label="Ayat" className="border-b border-[var(--border)]">
      <div ref={rail} onKeyDown={walk} className="strip-x relative gap-1 px-3 py-2">
        {Array.from({ length: count }, (_, i) => {
          const n = i + 1
          return (
            <button
              key={n}
              type="button"
              onClick={() => onPick(n)}
              tabIndex={n === here ? 0 : -1}
              aria-current={n === here ? 'location' : undefined}
              aria-label={n === open ? `${n}, being studied` : undefined}
              className={`press tap shrink-0 min-w-9 px-2 py-1 rounded-full type-small tabular-nums transition-colors
                ${n === open ? 'text-[var(--bg)] bg-[var(--c)]'
                  : n === here ? 'text-[var(--text)] bg-[var(--surface-hi)]'
                    : 'text-[var(--text-faint)] hover:text-[var(--text)]'}`}
            >
              {n}
            </button>
          )
        })}
      </div>
    </nav>
  )
}

/**
 * The one player for the surah, held to the bottom of the screen: back, play or
 * stop, on, and who is reciting. Playing runs on through the surah an ayah at a
 * time, and the list follows while the reader is following it.
 *
 * Who is reciting is the app's one dropdown (ui/WheelPicker), opening upwards
 * from the bar; its pill already names the voice, so the line beside the
 * buttons says only where the recitation is.
 */
function RecitationBar({ surah, count, from, here, recitation, reciter, onReciter, onFollow }) {
  const now = useSyncExternalStore(watch, nowPlaying, () => '')
  const [failed, setFailed] = useState(false)
  // The ayah last started and the address it was started on. Matched by that
  // address, not by asking the recitation again: the measured recording can
  // arrive mid-ayah and change what urlFor answers, but not what is playing.
  const [cue, setCue] = useState(null)
  const sounding = now && now === cue?.url ? cue.n : 0
  const at = sounding || from
  const { urlFor } = recitation

  const start = useCallback((n) => {
    if (n < 1 || n > count) return
    const url = urlFor(n)
    setFailed(false)
    setCue({ n, url })
    // A press that overtakes the last one aborts it; only a refusal is a failure.
    play(url).catch((e) => e.name !== 'AbortError' && setFailed(true))
  }, [count, urlFor])
  // A skip is the reader moving, so the list and rail go with it.
  const skipTo = (n) => { start(n); onFollow(n) }

  // On to the next ayah when one ends; the list follows only if the reader was
  // still with the one that finished, never pulled away from where they went.
  useEffect(() => watchEnd((url) => {
    if (url !== cue?.url || cue.n >= count) return
    start(cue.n + 1)
    if (Math.abs(here - cue.n) <= 1) onFollow(cue.n + 1)
  }), [cue, start, onFollow, here, count])
  // Stop when the bar goes with its surah, so nothing plays on under another.
  useEffect(() => () => stop(), [])

  const round = 'press shrink-0 grid place-items-center rounded-full transition-colors'
  const skip = `${round} w-8 h-8 text-[var(--text-dim)] hover:text-[var(--text)] disabled:opacity-30`

  return (
    <div className="reader-dock flex items-center gap-2 p-2 pl-3 border-t border-[var(--border)] bg-[var(--surface-hi)]">
      <button type="button" className={skip}
        onClick={() => skipTo(at - 1)} disabled={at <= 1} aria-label="Previous ayah">
        <Glyph d="M6 5h2v14H6zM20 5v14L9 12z" />
      </button>
      <button type="button" className={`${round} w-10 h-10 text-[var(--bg)] bg-[var(--c)]`}
        onClick={() => (sounding ? stop() : start(at))} onPointerEnter={() => prefetch(urlFor(at))}
        aria-label={sounding ? `Stop ${surah}:${sounding}` : `Play from ${surah}:${at}`}>
        <Glyph d={sounding ? 'M6 6h12v12H6z' : 'M7 4.5v15l13-7.5z'} />
      </button>
      <button type="button" className={skip}
        onClick={() => skipTo(at + 1)} disabled={at >= count} aria-label="Next ayah">
        <Glyph d="M16 5h2v14h-2zM4 5v14l11-7z" />
      </button>

      <p className="min-w-0 flex-1 truncate type-small" aria-live="polite">
        {failed ? (
          <span className="text-[var(--warn)]">That recitation could not be reached</span>
        ) : (
          <span className="font-mono text-[var(--text)]">{surah}:{at}</span>
        )}
      </p>

      <WheelPicker label="Reciter" options={VOICES} value={reciter} onChange={onReciter} className="shrink-0" />
    </div>
  )
}

function Glyph({ d }) {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d={d} /></svg>
  )
}

/** Back and on a surah. Its name is the picker's, just above, so not said twice. */
function Stepper({ surah, onChange }) {
  const arrow = `w-7 h-7 rounded-full border border-[var(--border)] text-[var(--text-dim)]
    hover:text-[var(--text)] hover:border-[var(--c)] disabled:opacity-30
    disabled:hover:border-[var(--border)] transition-colors shrink-0`
  return (
    <div className="flex items-center gap-2">
      <button type="button" className={arrow} onClick={() => onChange(surah - 1)}
        disabled={surah <= FIRST_SURAH} aria-label="Previous surah">‹</button>
      <button type="button" className={arrow} onClick={() => onChange(surah + 1)}
        disabled={surah >= LAST_SURAH} aria-label="Next surah">›</button>
    </div>
  )
}

