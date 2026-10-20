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
import { BOOKS } from '../lib/books'
import { DIFFICULTIES, printedPageOf, score } from '../lib/memorise'
import { PHONE, useMedia } from '../lib/useMedia'

import Line from './memorise/Line'
import ReciteStrip from './memorise/ReciteStrip'
import SimilarCards from './memorise/SimilarCards'
import EmptyState from './ui/EmptyState'
import Chip from './ui/Chip'
import ErrorAlert from './ui/ErrorAlert'
import PrimaryButton from './ui/PrimaryButton'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import SettingsPill from './ui/SettingsPill'
import WheelPicker from './ui/WheelPicker'
import { Skeleton } from './ui/Skeleton'
import {
  difficultyOf, HIDDEN, useAnswers, useArrivedPage, useBookPage, useGaps, useHowYouAnswer,
  usePageSteps, useReciteState, useReciteTurns, waysOf, withinPart,
} from './memorise/hooks'

export default function MemorisePanel({ accent, incoming, arrival, onVisit }) {
  const { answers, setAnswers, checked, setChecked, shown, setShown, fresh } = useAnswers()
  const { way, setWay, similar, hidden, difficulty, deal, chooseDifficulty, reDeal, chooseWay } = useHowYouAnswer(fresh)
  const {
    bookId, book, parts, part, data, isPending, isError, error, refetch, pages, page, pageNumber, meaning,
    setMeaning, pinned, openAt, openPart, openPage, openBook, pageOfLine,
  } = useBookPage({ fresh, setWay })
  // The mushaf page this one actually is, when the layout has been built. Null
  // means the pages were sized by word count, and saying "page 3 of 21" without
  // claiming a printed number is the honest thing to show for that.
  const printedPage = printedPageOf(page)
  const { recitedPage, reciting, startFrom, startLabel, show } = useReciteState({ page, book, pinned, shown, setShown })
  const { blanks, choices, twinsOfSurah, twinned, twinLines, twinQueries } = useGaps({
    data, page, part, pageNumber, deal, difficulty, way, similar, hidden, startFrom,
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
  const ways = waysOf(book)
  const missing = way === 'recite'
    ? [{ id: 'none', label: 'Show all' }, { id: HIDDEN, label: 'Hidden' }]
    : DIFFICULTIES.map((d) => ({ id: d.id, label: d.label }))
  const missingNow = way === 'recite' && difficulty !== 'none' ? HIDDEN : difficulty
  const practise = (
    <>
      <Segmented
        captioned={phone}
        wrap={phone}
        label="How you answer"
        options={ways}
        value={way}
        onChange={chooseWay}
        accent={accent}
      />
      {/* Reciting has two states worth choosing between, not five: the page
          read from, or the page said from memory. */}
      {!similar && (
        <Segmented
          captioned={phone}
          wrap={phone}
          label={way === 'recite' ? 'Words to say from memory' : 'How much is missing'}
          title={way === 'recite' ? undefined : difficultyOf(difficulty).title}
          options={missing}
          value={missingNow}
          onChange={chooseDifficulty}
          accent={accent}
        />
      )}
    </>
  )
  const pillWords = [ways.find((o) => o.id === way)?.label, !similar && missing.find((o) => o.id === missingNow)?.label].filter(Boolean)

  // Above the page and again under it, so a page read to its end turns from there.
  const pageSteps = (
    <span className="flex items-center gap-2">
      <Chip accent={accent} onClick={() => stepPage(-1)} disabled={atStart}>Previous</Chip>
      <Chip accent={accent} onClick={() => stepPage(1)} disabled={atEnd}>Next</Chip>
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

        {phone
          ? <SettingsPill label={pillWords.join(' · ')} title="How you answer" align="start">{practise}</SettingsPill>
          : practise}
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
              {/* Reciting says what to do in its own dock; typing has one
                  thing worth knowing first. */}
              {way !== 'recite' && (way === 'type' || similar) && (
                <span className="text-[var(--text-faint)]">vowels not needed</span>
              )}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {/* Only when there is something covered to uncover. Two sizes
                  of help, because being stuck on one word and having lost the
                  thread of a whole ayah are not the same trouble. What they
                  give is marked as given, never as recited. */}
              {way !== 'recite' && !similar && (
                <Chip accent={accent} onClick={reDeal}>New gaps</Chip>
              )}
              {/* Off to start with, and that is the point: "Say He (is) Allah
                  the One" names both words missing from 112:1. It is here for
                  when you are stuck, not for while you are trying. */}
              <Chip accent={accent} onClick={() => setMeaning((on) => !on)}>
                {meaning ? 'Hide translation' : 'Show translation'}
              </Chip>
            </div>
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
