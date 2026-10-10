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
import { Fragment } from 'react'

import { isQuranic, recitedForm } from '../lib/arabicText'
import { BOOKS } from '../lib/books'
import { DIFFICULTIES, isRight, printedPageOf, score, wordsOf } from '../lib/memorise'

import { LOOK, SHOWN } from '../lib/reciteColors'

import ArabicText from './ui/ArabicText'
import AyahNumber from './ui/AyahNumber'
import ReciteStrip from './memorise/ReciteStrip'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import PrimaryButton from './ui/PrimaryButton'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import TwinCards from './ui/TwinCard'
import WheelPicker from './ui/WheelPicker'
import { Skeleton } from './ui/Skeleton'
import {
  difficultyOf, HIDDEN, useAnswers, useArrivedPage, useBookPage, useGaps, useHowYouAnswer,
  usePageSteps, useReciteState, useReciteTurns, WAYS, withinPart,
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
