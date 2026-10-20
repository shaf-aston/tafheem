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
import { useState } from 'react'

import { BOOKS } from '../lib/books'
import { DIFFICULTIES, printedPageOf, score } from '../lib/memorise'
import { PHONE, useMedia } from '../lib/useMedia'

import Line from './memorise/Line'
import ReciteStrip from './memorise/ReciteStrip'
import SettingsSheet from './memorise/SettingsSheet'
import EmptyState from './ui/EmptyState'
import Chip from './ui/Chip'
import ErrorAlert from './ui/ErrorAlert'
import PrimaryButton from './ui/PrimaryButton'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import Stepper from './ui/Stepper'
import WheelPicker from './ui/WheelPicker'
import { Skeleton } from './ui/Skeleton'
import {
  difficultyOf, HIDDEN, useAnswers, useArrivedPage, useBookPage, useGaps, useHowYouAnswer,
  usePageSteps, useReciteState, useReciteTurns, waysOf, withinPart,
} from './memorise/hooks'

export default function MemorisePanel({ accent, incoming, arrival, onVisit }) {
  const { answers, setAnswers, checked, setChecked, shown, setShown, fresh } = useAnswers()
  const { way, setWay, hidden, difficulty, deal, chooseDifficulty, reDeal, chooseWay } = useHowYouAnswer(fresh)
  const {
    bookId, book, parts, part, data, isPending, isError, error, refetch, pages, page, pageNumber, meaning,
    setMeaning, pinned, openAt, openPart, openPage, openBook, pageOfLine,
  } = useBookPage({ fresh, setWay })
  // The mushaf page this one actually is, when the layout has been built. Null
  // means the pages were sized by word count, and saying "page 3 of 21" without
  // claiming a printed number is the honest thing to show for that.
  const printedPage = printedPageOf(page)
  const { recitedPage, reciting, startFrom, startLabel, show } = useReciteState({ page, book, pinned, shown, setShown })
  const { blanks, choices } = useGaps({
    data, page, pageNumber, deal, difficulty, way, hidden, startFrom,
  })
  const marks = page ? score(page, blanks, answers) : { right: 0, total: 0 }
  const { partBy, stepPage, atStart, atEnd, swipe, slide } = usePageSteps({ parts, part, pages, pageNumber, bookId, pageOfLine, openPage, openPart })
  const { card, listen, elsewhere, where, askToGo, goElsewhere, setStayed } = useReciteTurns({
    way, hidden, reciting, recitedPage, bookId, part, pageNumber, pinned, pages, partBy, openPart, pageOfLine,
  })
  useArrivedPage({ arrival, incoming, onVisit, bookId, part, page, pageOfLine, openBook, openPart })

  // How you practise, chosen once and left: beside the pickers on a wide screen,
  // behind one pill on a phone, where the pickers and both of these were three
  // rows before the page began.
  const phone = useMedia(PHONE)
  // The word or ayah whose card is open: { at } or { line }. Only a place; the
  // card reads the live marks, so what it shows keeps up with the recitation.
  const [asked, setAsked] = useState(null)
  // Closed by the reader, Esc or a press outside (MarkCard), and here by a page
  // turn or by stopping; never by a mark changing under it. A card is stamped
  // with the page and listening state it was opened in, and only counts while
  // they are unchanged.
  const stamp = `${bookId}/${part}/${pageNumber}/${reciting.listening}`
  const opened = asked?.stamp === stamp ? asked : null
  const setOpen = (place) => setAsked(place && { ...place, stamp })
  const ways = waysOf(book)
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
      wrap={phone}
      label={missingLabel}
      title={way === 'recite' ? undefined : difficultyOf(difficulty).title}
      options={missing}
      value={missingNow}
      onChange={chooseDifficulty}
      accent={accent}
    />
  )
  // On a phone the book, the gaps and the translation wait in one sheet, so
  // the rows over the page are the way you answer, the surah and the page.
  const settingsRows = [
    { caption: 'Book', control: <Segmented label="Book" options={Object.values(BOOKS)} value={bookId} onChange={openBook} accent={accent} /> },
    missingSwitch && { caption: missingLabel, control: missingSwitch },
    { caption: 'Translation', control: <Segmented label="Translation" options={[{ id: false, label: 'Off' }, { id: true, label: 'On' }]} value={meaning} onChange={setMeaning} accent={accent} /> },
  ].filter(Boolean)
  const settingsWords = [book.label, missing.find((o) => o.id === missingNow)?.label].filter(Boolean)

  // Above the page and again under it, so a page read to its end turns from there.
  const pageSteps = (
    <span className="flex items-center gap-2">
      <Chip accent={accent} onClick={() => stepPage(-1)} disabled={atStart}>Previous</Chip>
      <Chip accent={accent} onClick={() => stepPage(1)} disabled={atEnd}>Next</Chip>
    </span>
  )

  return (
    <div className="panel" {...swipe}>
      {/* No subtitle: "fill in the gaps" was wrong for reciting, and the way
          switch under it already says what each way is. */}
      <SectionHeader emblem="mem" title="Memorise" arabic="حفظ" />

      {/* One row, no captions: each control's choices already say what it is,
          and the captions were a second row of grey restating them. Their
          words stay as screen-reader labels and hover titles. */}
      {/* On a phone: the way you answer, always in sight, then the part and
          one pill for what is chosen once and left (book, gaps, translation). */}
      {phone && answerWay}
      <div className="flex flex-wrap items-center gap-2">
        {!phone && (
          <WheelPicker label="Book" options={Object.values(BOOKS)} value={bookId} onChange={openBook} accent={accent} />
        )}

        <WheelPicker
          label={book.partLabel}
          options={parts ?? []}
          value={part}
          onChange={openPart}
          accent={accent}
          className="max-w-[18rem]"
        />

        {phone
          ? <SettingsSheet label={settingsWords.join(' · ')} rows={settingsRows} accent={accent} />
          : <>{answerWay}{missingSwitch}</>}
      </div>

      {isPending && <Skeleton className="h-40 w-full" />}

      {isError && (
        <ErrorAlert title="That part could not be read" error={error} fallback="The text comes from the Qur\'an tab\'s own source." onRetry={refetch} />
      )}

      {data && pages.length === 0 && <EmptyState>Nothing to memorise here.</EmptyState>}

      {page && (
        <>
          {/* One wrapping row: the page and its arrows, then what helps. */}
          <div className="flex items-center gap-2 flex-wrap text-sm text-[var(--text-dim)]">
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
            <span className="flex-1" />
            {/* Only when there is something covered to uncover. Two sizes
                of help, because being stuck on one word and having lost the
                thread of a whole ayah are not the same trouble. What they
                give is marked as given, never as recited. */}
            {way !== 'recite' && (
              <Chip accent={accent} onClick={reDeal}>New gaps</Chip>
            )}
            {/* Off to start with, and that is the point: "Say He (is) Allah
                the One" names both words missing from 112:1. It is here for
                when you are stuck, not for while you are trying. */}
            {!phone && (
              <Chip accent={accent} onClick={() => setMeaning((on) => !on)}>
                {meaning ? 'Hide translation' : 'Show translation'}
              </Chip>
            )}
            {/* Reciting says what to do in its own dock; typing has one
                thing worth knowing first. */}
            {way === 'type' && (
              <span className="basis-full sm:basis-auto text-[var(--text-faint)]">vowels not needed</span>
            )}
          </div>

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

          <div ref={card} data-recite-page="" key={`${bookId}/${part}/${pageNumber}`} {...slide}
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
          <div className="flex justify-center">{pageSteps}</div>
        </>
      )}
    </div>
  )
}
