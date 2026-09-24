/**
 * What a root has meant since the beginning, the classical, lughawi sense.
 *
 * The dictionary underneath says what each *word* means today. This says what
 * the three letters themselves have meant, which is a different question and is
 * kept in its own card so the two are never read as one answer.
 *
 * The book is Ibn Faris's Maqayees al-Lugha and it is not shipped with the app.
 * Until it is installed this card exists to say exactly that. It must never be
 * possible to read "we don't have the book" as "this root has no origin sense", 
 * so the three situations get three different sentences, and the card always
 * prints the letters that were actually searched.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getRootEntryEnglish, getRootEntryLines, getRootMeaning } from '../api'
import { smartError } from '../lib/apiError'
import { entryLines } from '../lib/entryLines'
import { BROKEN, MISSING, READY } from '../lib/rootMeaningStatus'
import { useHealth } from '../lib/useHealth'

import ArabicText from './ui/ArabicText'
import ShowRest from './ui/ShowRest'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import Segmented from './ui/Segmented'
import { Skeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'

/** Sentence punctuation, Arabic and Latin, at the start of what is left over. */
const LEADING_PUNCTUATION = /^[.،؛:\s]+/
/** Whether anything but that punctuation is left, otherwise there is no rest. */
const HAS_WORDS = /[^.،؛:\s]/

export default function RootMeaningCard({ root: asked, hasAlternates, accent }) {
  const { rootMeaningStatus, healthFailed, retryHealth } = useHealth()

  const installed = rootMeaningStatus === READY

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['root-meaning', asked],
    queryFn: () => getRootMeaning(asked),
    // Nothing to ask when the book is not on this machine: the message below
    // already says so, and a request would only come back as an empty answer.
    enabled: installed && Boolean(asked),
    staleTime: Infinity,
  })

  if (!asked) return null

  return (
    <section
      className="p-4 rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)] space-y-3"
      aria-label="Classical root sense"
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          {/* The book's name is in the heading, not only in the badge: a reader
              scanning the page for classical dictionaries counted three below and
              missed this one, which is the fourth. */}
          <h3 className="type-body font-medium text-[var(--text)]">
            Classical root sense: Maqayees al-Lugha (Ibn Faris)
          </h3>
        </div>
        {/* The same badge every other panel names its source with, rather than
            this card's own wording for the same thing, one shape to learn, and
            the book's standing is stated in the same terms as everyone else's.
            Every source on the card wears that badge and nothing else: a mark
            beside one of them and not the others read as a difference in
            standing that is not there. */}
        <SourceBadge source={data?.source} className="shrink-0" />
      </div>

      {/* The body swaps between three different answers, and swaps again when
          the root above is changed. Announced politely so the change is not
          silent to anyone who cannot see it happen. */}
      <div aria-live="polite">
        <Body
          // The answer the backend just sent wins over the check made when the
          // page opened: the book can be installed, or fail, after that check.
          status={data?.status ?? rootMeaningStatus}
          healthFailed={healthFailed}
          onRetryHealth={retryHealth}
          asked={data?.root || asked}
          data={data}
          isPending={isPending}
          isError={isError}
          error={error}
          onRetry={refetch}
          accent={accent}
          hasAlternates={hasAlternates}
        />
      </div>
    </section>
  )
}

function Body({
  status, healthFailed, onRetryHealth,
  asked, data, isPending, isError, error, onRetry, accent, hasAlternates,
}) {
  // Whether the rest of the entry is open. The English reading below it is
  // fetched on that alone, so a root looked up and never opened costs nothing.
  const [opened, setOpened] = useState(false)

  // How the panel reads: the book whole with its English after it, or the two
  // interleaved, one English line under each Arabic line. Together is the
  // default because it is the book as printed; the pairing is a convenience.
  const [view, setView] = useState('together')

  // Asked and got no answer at all. Say so, rather than showing a loading bar
  // that never ends because nothing is still on its way.
  if (healthFailed) {
    return (
      <ErrorAlert title="Couldn't reach the backend">
        Nothing can be said about <Letters value={asked} /> until the backend answers.
        This is not a statement about the root or about the book.
        <RetryButton onClick={onRetryHealth} />
      </ErrorAlert>
    )
  }

  if (status === null) return <Skeleton className="h-4 w-2/3" />

  if (status === MISSING) {
    return (
      <Note>
        The Maqayees al-Lugha entries aren't on this machine yet, so there is nothing to show
        here. This is not a statement about <Letters value={asked} />. Put the extracted file
        in place, restart the backend, then reload this page.
      </Note>
    )
  }

  // A file that is present but unreadable is a failure, not an empty result, and
  // gets the same loud banner as any other failure in the app.
  if (status === BROKEN) {
    return (
      <ErrorAlert title="Classical entries could not be read">
        A Maqayees file is installed but could not be read, so nothing is shown rather than
        something possibly wrong. The backend log says which file and why.
      </ErrorAlert>
    )
  }

  // Anything that is not one of the three above, a backend newer than this
  // page, or a rename that only landed on one side. Everything below assumes
  // the book is loaded, and the first thing below says the book has no entry
  // for this root: a claim about the book, made because a word did not match.
  if (status !== READY) {
    return (
      <ErrorAlert title="Unexpected answer about the book">
        The backend reported a state this page does not know, so nothing is shown about{' '}
        <Letters value={asked} /> rather than something possibly wrong.
      </ErrorAlert>
    )
  }

  if (isPending) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-3 w-1/4" />
        <Skeleton className="h-6 w-3/4" />
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorAlert title="Classical lookup failed">
        {smartError(error, 'The backend may have stopped since this page was opened.')}
        <RetryButton onClick={onRetry} />
      </ErrorAlert>
    )
  }

  if (!data?.meaning) {
    return (
      <Note>
        Searched <Letters value={asked} />, and the book has no entry under those letters. It may be
        written differently there, so try the bare three letters
        {hasAlternates ? ', or one of the roots above.' : '.'}
      </Note>
    )
  }

  const { core_meaning, sarf_pattern, variances, body, english } = data.meaning
  // The entry always opens with the origin sense, so showing both in full would
  // print it twice. What is left is the rest of the entry, and for 226 roots
  // that is only the full stop the sense ended on, which must not open a panel
  // onto a single piece of punctuation.
  const tail = body?.startsWith(core_meaning) ? body.slice(core_meaning.length) : body
  const rest = HAS_WORDS.test(tail || '') ? tail.replace(LEADING_PUNCTUATION, '') : ''

  return (
    <div className="space-y-3">
      <div>
        <div className="type-small text-[var(--text-faint)] mb-1">
          Origin sense of <Letters value={asked} />
        </div>
        {/* The book spells some roots with a hamza where a reader would not, so
            the letters searched and the letters answered are not always the
            same. Saying which one answered is the difference between showing
            an entry and quietly substituting one root for another. */}
        {data.book_root && (
          <p className="type-small text-[var(--text-faint)] mb-1">
            The book spells this root <Letters value={data.book_root} />, and that is the entry below.
          </p>
        )}
        {/* Capped to a readable measure, like the panel subtitles: a long
            classical definition set across the full card is a line the eye
            loses its place on. ml-auto is deliberately physical: this element is
            itself right-to-left, so the logical ms-auto pushed it the wrong way. */}
        {/* The sense itself sometimes ends on a line of verse the book cites,
            so it is laid out line by line for the same reason the rest is. */}
        <div className="space-y-1">
          <Lines text={core_meaning} size="base" style={{ color: accent }} />
        </div>
      </div>

      {/* The English sits under its own badge, not the card's. The Arabic above
          was typed by a person; this was read off a photograph of the page by a
          machine, and one badge covering both would lend the weaker the standing
          of the stronger. */}
      {english && (
        <div className="space-y-1.5">
          <p className="text-sm text-[var(--text-dim)] max-w-prose">{english}</p>
          {/* Pushed to the same edge the card's own badge sits on, so the two
              read as one column of sources rather than one label adrift in the
              middle of the card. */}
          <SourceBadge source={data.english_source} className="ms-auto flex" />
        </div>
      )}

      {sarf_pattern && (
        <div className="flex items-baseline gap-1.5 flex-wrap">
          <span className="type-small text-[var(--text-faint)]">Pattern</span>
          <ArabicText>{sarf_pattern}</ArabicText>
        </div>
      )}

      {variances?.length > 0 && (
        <div>
          <div className="type-small text-[var(--text-faint)] mb-1">Branches of that sense</div>
          {/* dir on the list, not on each row: every Arabic line in this card
              then sits against the same edge as the origin sense above it. A
              flex row reversed the numbering to the far side and left the two
              halves of the card aligned against opposite edges. */}
          <ol className="space-y-1 text-right" dir="rtl">
            {variances.map((v, i) => (
              <li key={i}>
                <span className="type-small text-[var(--text-faint)] ml-2">{i + 1}.</span>
                <ArabicText size="sm">{v}</ArabicText>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* The rest of the entry: Ibn Faris's examples, the verses he cites with
          their references, the poetry. Kept whole and shown as prose, he marks
          where one sense ends in only a minority of entries, so cutting it into
          pieces would mean printing a guess at where his meaning stops.

          On the page, cut to a few lines rather than shut behind a drop-down.
          A label alone said nothing about what was under it, and a reader
          looking up one root had several of these to press through before any
          book spoke. A snippet answers "is this what I came for" without the
          press.

          The English reading, and the view toggle, arrive on that press.
          Reading it costs a call to a model, so it waits to be asked for; the
          Arabic beside it costs nothing and is already there. */}
      {rest && (
        <div className="space-y-3 text-[var(--text-dim)]">
          <h4 className="type-small text-[var(--text-faint)]">The rest of the entry</h4>

          {opened && (
            <Segmented
              label="How to read the entry"
              accent={accent}
              options={[
                { id: 'together', label: 'Together' },
                { id: 'lines', label: 'Line by line' },
              ]}
              value={view}
              onChange={setView}
            />
          )}

          {opened && view === 'lines' ? (
            // Keyed by the root so asking about a different one starts this
            // over, rather than showing a reading nobody asked for.
            <EntryLineByLine key={data.root} root={data.root} enabled={opened} />
          ) : (
            <ShowRest lines={6} accent={accent} onOpen={() => setOpened(true)}>
              {/* The book first, its reading under it. This panel is the
                  book's own words; the English is what a machine made of them,
                  and printing the machine first put a retelling where the
                  reader came looking for the text. */}
              <Lines text={rest} />
            </ShowRest>
          )}

          {opened && view === 'together' && (
            <EntryEnglish key={data.root} root={data.root} enabled={opened} />
          )}
        </div>
      )}

    </div>
  )
}

/**
 * The whole entry retold in English, when the reader asks for it.
 *
 * The gloss higher up the card covers the origin sense only. Everything below
 * it, the examples, the verses, the poetry; is untranslated, which is a wall
 * to anyone who cannot read classical Arabic.
 *
 * It costs a call to a model to make, so nothing is fetched until the entry is
 * opened, but opening the entry is the whole request, and a second button in
 * front of the answer is a riddle rather than a saving. When it arrives it
 * carries its own badge saying a machine wrote it, and it is never allowed to
 * replace the Arabic beside it.
 */
function EntryEnglish({ root, enabled }) {
  const { data, isFetching, isError, error, refetch } = useQuery({
    queryKey: ['root-entry-english', root],
    queryFn: () => getRootEntryEnglish(root),
    enabled,
    staleTime: Infinity,
    // One failed reading is one failed reading. Retrying spends more calls on
    // the same answer, and the message below already offers to try again.
    retry: false,
  })

  if (!enabled) return null

  if (isFetching) return <Skeleton className="h-4 w-1/2" />

  if (isError) {
    return (
      <ErrorAlert title="Couldn't put this into English">
        {smartError(error, 'The Arabic below is unaffected.')}
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }

  if (!data?.english) return null

  return (
    <div className="space-y-1.5">
      {/* The longest entries run past what the model is handed. Saying so is the
          difference between a short retelling and a retelling that stops. */}
      {data.truncated && (
        <p className="type-small text-[var(--text-faint)]">
          The entry was longer than could be read at once, so this covers its opening.
        </p>
      )}
      <p className="text-sm text-[var(--text-dim)] max-w-prose whitespace-pre-line">
        {data.english}
      </p>
      <SourceBadge source={data.source} className="ms-auto flex" />
    </div>
  )
}

/**
 * The same entry with its English interleaved, one line under each Arabic line.
 *
 * The backend does the pairing and refuses an answer it could not line up, so
 * every English line printed here belongs to the Arabic line above it. When
 * that refusal happens, this shows the refusal and nothing else: the Together
 * view is one press away and unaffected, and the error says so.
 */
function EntryLineByLine({ root, enabled }) {
  const { data, isFetching, isError, error, refetch } = useQuery({
    queryKey: ['root-entry-lines', root],
    queryFn: () => getRootEntryLines(root),
    enabled,
    staleTime: Infinity,
    // One failed pairing is one failed pairing. The message below offers to
    // try again, and the Together view still has the whole entry.
    retry: false,
  })

  if (!enabled) return null

  if (isFetching) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorAlert title="Couldn't line the English up">
        {smartError(error, 'The backend may have stopped since this page was opened.')}
        {' '}The Together view above still shows the whole entry.
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }

  if (!data?.lines?.length) return null

  return (
    <div className="space-y-1.5">
      {data.truncated && (
        <p className="type-small text-[var(--text-faint)]">
          The entry was longer than could be read at once, so this covers its opening.
        </p>
      )}
      {/* Facing columns. The Arabic keeps the right, where every other piece of
          Arabic on this card sits, and the English takes the width beside it
          that used to be empty. Level with each other, and numbered, so the eye
          can cross the gutter and land on the right line.

          On a narrow screen there is only one column, so the two go back to
          sitting one under the other: that is why the Arabic is written first
          here and the wide layout puts it on the right, rather than the markup
          being ordered for the wide case and reading backwards on a phone. */}
      <ol className="space-y-0">
        {data.lines.map((pair, i) => (
          <li
            key={i}
            className="grid gap-x-8 gap-y-1 py-3 border-t border-[var(--border)] first:border-t-0
              sm:grid-cols-[1fr_1.1fr]"
          >
            <span
              className="type-micro tabular-nums uppercase tracking-[0.14em] text-[var(--text-faint)]
                sm:[grid-area:1/1/2/-1]"
            >
              {String(i + 1).padStart(2, '0')}
            </span>
            {/* The Arabic through the same layout as the Together view, so a
                verse keeps its two halves; only where it sits is new. */}
            <div className="sm:[grid-area:2/2] min-w-0">
              <Lines text={pair.arabic} />
            </div>
            <p className="text-sm text-[var(--text-dim)] sm:[grid-area:2/1] self-start" dir="ltr">
              {pair.english}
            </p>
          </li>
        ))}
      </ol>
      <SourceBadge source={data.source} className="ms-auto flex" />
    </div>
  )
}

/**
 * One line of the entry, laid out the way the book lays it out.
 *
 * A verse is one thought in two halves with a gap down the middle of the page,
 * and printing it as a sentence loses the shape that makes it readable as
 * poetry. Everything else is prose and stays against the right edge with the
 * origin sense above it.
 */
const Line = ({ line, size = 'sm', style }) => (line.halves ? (
  <div
    className="max-w-prose ml-auto flex flex-wrap justify-center gap-x-10 gap-y-1 leading-loose"
    dir="rtl"
    style={style}
  >
    {line.halves.map((half, i) => <ArabicText key={i} size={size}>{half}</ArabicText>)}
  </div>
) : (
  <ArabicText as="p" size={size} className="max-w-prose ml-auto leading-loose" style={style}>
    {line.text}
  </ArabicText>
))

/** Every line of a passage, laid out. The card's two Arabic passages share it. */
const Lines = ({ text, size, style }) =>
  entryLines(text).map((line, i) => <Line key={i} line={line} size={size} style={style} />)

/** Explanatory prose. Body text, so it keeps the reading size the panels use. */
const Note = ({ children }) => <p className="text-sm text-[var(--text-dim)]">{children}</p>

/** The exact letters searched, shown so a spelling mismatch is visible, not guessed at. */
const Letters = ({ value }) => <ArabicText size="sm" className="text-[var(--text)]">{value}</ArabicText>
