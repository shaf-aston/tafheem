/**
 * Memorise, a page of a book with words taken out, for you to put back.
 *
 * The reader picks a book, a part of it, how much to take out, and whether to
 * type each missing word or choose it from a short list; the page is then
 * shown as it is printed, with a gap where each missing word was. Nothing is
 * marked until the whole page is checked at once, because stopping to be told
 * after every word turns recitation into a series of separate questions.
 *
 * The rules for what a page is and which words go are in lib/memorise/memorise.js, with
 * no knowledge of the screen; the books are in lib/memorise/books.js, with no knowledge
 * of either. This file only shows what those two decide.
 */
import { useRef } from 'react'

import { BOOKS } from '../../lib/memorise/books'
import { DIFFICULTIES, printedPageOf, score } from '../../lib/memorise/memorise'
import { PHONE, useMedia } from '../../lib/hooks/useMedia'

import { nextGapOnEnter } from './gapKeys'
import Line from './Line'
import ReciteStrip from './ReciteStrip'
import SettingsSheet from './SettingsSheet'
import EmptyState from '../ui/feedback/EmptyState'
import Chip from '../ui/inputs/Chip'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import PrimaryButton from '../ui/buttons/PrimaryButton'
import SectionHeader from '../ui/display/SectionHeader'
import Segmented from '../ui/inputs/Segmented'
import Stepper from '../ui/inputs/Stepper'
import WheelPicker from '../ui/inputs/WheelPicker'
import { Skeleton } from '../ui/feedback/Skeleton'
import {
  difficultyOf, HIDDEN, useArrivedPage, useBookPage, useGaps, useHowYouAnswer,
  usePageSteps, WAYS, withinPart,
} from './hooks'
import { useOpenCard, useReciteState, useReciteTurns } from './useRecite'
import { gapsScope, useAnswers } from './useAnswers'
import useFollowScroll from './useFollowScroll'

export default function MemorisePanel({ accent, incoming, arrival, onVisit }) {
  const { way, hidden, difficulty, deal, chooseDifficulty, reDeal, chooseWay } = useHowYouAnswer()
  const {
    bookId, book, parts, part, data, isPending, isError, error, refetch, pages, page, pageNumber, meaning,
    setMeaning, pinned, openAt, openPart, openPage, openBook, pageOfLine,
  } = useBookPage({ incoming })
  const { answers, setAnswers, checked, setChecked, shown, setShown, fresh } = useAnswers(
    gapsScope({ bookId, part, pageNumber, way, difficulty, deal, pinned }),
  )
  // The mushaf page this one actually is, when the layout has been built. Null
  // means the pages were sized by word count, and saying "page 3 of 21" without
  // claiming a printed number is the honest thing to show for that.
  const printedPage = printedPageOf(page)
  const { recitedPage, reciting, startFrom, startLabel, show } = useReciteState({ page, book, pinned, shown, setShown })
  const { blanks, choices } = useGaps({
    data, page, pageNumber, deal, difficulty, way, hidden, startFrom, pinned,
  })
  const marks = page ? score(page, blanks, answers) : { right: 0, total: 0 }
  const landing = useArrivedPage({ arrival, incoming, onVisit, bookId, part, page, pageOfLine, openBook, openPart })
  const card = useRef(null)
  const { partBy, stepPage, atStart, atEnd, swipe, slide } = usePageSteps({ card, parts, part, pages, pageNumber, bookId, pageOfLine, openPage, openPart, landing })
  const { listen, elsewhere, where, askToGo, goElsewhere, setStayed } = useReciteTurns({
    card, way, hidden, reciting, recitedPage, bookId, part, pageNumber, pinned, pages, partBy, openPart, pageOfLine,
  })
  useFollowScroll(card, reciting.marks.at, reciting.listening)

  // How you practise is chosen once and left, so it waits behind one Settings
  // pill on every screen: four rows of controls stood between the tab and the
  // first ayah.
  const phone = useMedia(PHONE)
  const [opened, setOpen] = useOpenCard(`${bookId}/${part}/${pageNumber}/${reciting.listening}`)
  const ways = WAYS
  const missing = way === 'recite'
    ? [{ id: 'none', label: 'Show all' }, { id: HIDDEN, label: 'Hidden' }]
    : DIFFICULTIES.map((d) => ({ id: d.id, label: d.label }))
  const missingNow = way === 'recite' && difficulty !== 'none' ? HIDDEN : difficulty
  const answerWay = (
    <Segmented
      fill={phone}
      label="How you answer"
      options={ways}
      value={way}
      onChange={chooseWay}
      accent={accent}
    />
  )
  // Reciting has two states worth choosing between, not five: the page read
  // from, or the page said from memory.
  const missingLabel = way === 'recite' ? 'Words to say from memory' : 'How much is missing'
  const missingSwitch = (
    <Segmented
      label={missingLabel}
      title={way === 'recite' ? undefined : difficultyOf(difficulty).title}
      options={missing}
      value={missingNow}
      onChange={chooseDifficulty}
      accent={accent}
    />
  )
  const settingsRows = [
    { caption: 'How you answer', control: answerWay },
    { caption: 'Book', control: <Segmented label="Book" options={Object.values(BOOKS)} value={bookId} onChange={openBook} accent={accent} /> },
    missingSwitch && { caption: missingLabel, control: missingSwitch },
    { caption: 'Translation', control: <Segmented label="Translation" options={[{ id: false, label: 'Off' }, { id: true, label: 'On' }]} value={meaning} onChange={setMeaning} accent={accent} /> },
  ].filter(Boolean)
  const settingsWords = [book.label, missing.find((o) => o.id === missingNow)?.label].filter(Boolean)

  // Above the page and again under it, so a page read to its end turns from there.
  const pageSteps = (
    <span className="tap-thumb flex items-center gap-4">
      <Chip accent={accent} onClick={() => stepPage(-1)} disabled={atStart}>Previous</Chip>
      <Chip accent={accent} onClick={() => stepPage(1)} disabled={atEnd}>Next</Chip>
    </span>
  )

  return (
    <div className="panel" {...swipe}>
      {/* No subtitle: "fill in the gaps" was wrong for reciting, and the way
          switch under it already says what each way is. */}
      <SectionHeader tab="mem" />

      {/* One quiet row, so the page comes first: where you are (part, page)
          and one Settings pill for everything chosen once and left. */}
      <div className="mem-bar tap-thumb">
        <WheelPicker
          label={book.partLabel}
          options={parts ?? []}
          value={part}
          onChange={openPart}
          accent={accent}
          className="max-w-[18rem]"
        />
        {page && !landing && (
          <>
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
            <Stepper label="page"
              onPrev={atStart ? null : () => stepPage(-1)}
              onNext={atEnd ? null : () => stepPage(1)} />
          </>
        )}
        <span className="flex-1" />
        <SettingsSheet summary={settingsWords.join(' · ')} rows={settingsRows} accent={accent} />
      </div>

      {(isPending || landing) && <Skeleton className="h-40 w-full" />}

      {isError && (
        <ErrorAlert title="That part could not be read" error={error} fallback="The text comes from the Qur\'an tab\'s own source." onRetry={refetch} />
      )}

      {data && !landing && pages.length === 0 && <EmptyState>Nothing to memorise here.</EmptyState>}

      {page && !landing && (
        <>
          {/* Mounted always, so a screen reader hears the question when it
              appears; empty, it takes no room. */}
          <div role="status" className="empty:absolute">
            {askToGo && (
              <div className="flex items-center gap-3 flex-wrap">
                <span className="type-small text-[var(--text-dim)]">You seem to be reciting {where}.</span>
                <Chip accent={accent} onClick={goElsewhere}>Go there</Chip>
                <Chip accent={accent} onClick={() => setStayed(elsewhere.surah)}>Stay</Chip>
              </div>
            )}
          </div>

          <div ref={card} data-recite-page="" key={`${bookId}/${part}/${pageNumber}`} {...slide} onKeyDown={nextGapOnEnter}
            className={`rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-4 scroll-mt-[calc(var(--app-header-h,0px)+1rem)] ${slide.className}`}>
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
                  recite={way === 'recite'
                    ? { ...reciting.marks, from: recitedPage.lines[l].from, shown, open: opened, setOpen, takeAudio: reciting.takeAudio }
                    : null}
                  // Pressable while listening too: jumping back or ahead must not
                  // mean stopping first. forget() keeps the microphone running.
                  onStartAt={way === 'recite' ? openAt : null}
                  onAnswer={(key, value) => setAnswers((was) => ({ ...was, [key]: value }))}
                />
              ))}
            </div>
            {/* Run on, a line has nowhere under it for its English, so the
                page's translation follows the Arabic. Newspaper columns fill the
                width however long each ayah is, one column on a phone. */}
            {book.flow && meaning && (
              <ol className="columns-[22rem] gap-x-10">
                {page.filter((line) => line.english).map((line) => (
                  <li key={line.id} className="type-body text-[var(--text-dim)] leading-relaxed break-inside-avoid mb-2">
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
              transcript={reciting.transcript}
              marks={reciting.marks}
              lines={recitedPage.lines}
              accent={accent}
              status={reciting.marks.began != null ? `Following you from ${startLabel}` : 'Or tap any word to begin there'}
              // Two sizes of help, because being stuck on one word and having
              // lost the thread of a whole ayah are not the same trouble. What
              // they give is marked as given, never as recited.
              help={hidden ? [
                { label: 'Show a word', onClick: () => show(false) },
                { label: 'Show this ayah', onClick: () => show(true) },
              ] : null}
              onStart={listen}
              onStop={reciting.stop}
              onStartAt={openAt}
            />
          ) : blanks.size === 0 ? (
            // Two different reasons land here: the reader chose "None" to just
            // read the page, or every line on it is one word long so there was
            // nothing to take out even at a harder setting. Only the second is
            // worth saying, the first is exactly what was asked for.
            difficulty !== 'none' && (
              <EmptyState>
                Every line here is one word long, so there is nothing to take out.
              </EmptyState>
            )
          ) : (
            <div className="space-y-2">
              {/* Reciting says what to do in its own dock; typing has one
                  thing worth knowing first. */}
              {way === 'type' && !checked && (
                <p className="type-small text-center text-[var(--text-faint)]">vowels not needed</p>
              )}
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
                <p className="type-ui text-center text-[var(--text-dim)]" aria-live="polite">
                  {marks.right} of {marks.total} right
                  {marks.right < marks.total && ', the missed words are shown above'}
                </p>
              )}
            </div>
          )}
          {/* New gaps sits with the page turns, under the page: both are
              "another go", and neither needs to stand above the first ayah. */}
          <div className="tap-thumb flex justify-center gap-4 flex-wrap">
            {way !== 'recite' && <Chip accent={accent} onClick={reDeal}>New gaps</Chip>}
            {pageSteps}
          </div>
        </>
      )}
    </div>
  )
}
