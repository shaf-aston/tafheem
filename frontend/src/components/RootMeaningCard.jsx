/**
 * What a root has meant since the beginning, the classical, lughawi sense.
 *
 * The dictionary underneath says what each *word* means today. This says what
 * the three letters themselves have meant, which is a different question and is
 * kept in its own card so the two are never read as one answer.
 *
 * The book is Ibn Faris's Maqayees al-Lugha. Where it is not installed the card
 * says so. It must never be possible to read "we don't have the book" as "this
 * root has no origin sense",
 * so the three situations get three different sentences, and the card always
 * prints the letters that were actually searched.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getRootEntryEnglish, getRootEntryLines, getRootMeaning } from '../api'
import config from '../dictionary.json'
import { BROKEN, MISSING, READY } from '../lib/loadStatus'
import { useHealth } from '../lib/useHealth'
import { useRemembered } from '../lib/useRemembered'

import { Lines } from './EntryArabic'
import { LinePage, LineSpotlight } from './EntryLines'
import ArabicText from './ui/ArabicText'
import ShowRest from './ui/ShowRest'
import ErrorAlert from './ui/ErrorAlert'
import Segmented from './ui/Segmented'
import { Skeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'

/**
 * The rest of the entry in English, in two shapes (read three ways, see VIEWS).
 * Both cost a model call, so neither retries: the message offers to try again.
 */
const ENGLISH = {
  together: {
    key: 'root-entry-english',
    get: getRootEntryEnglish,
    failed: "Couldn't put this into English",
    fallback: 'The Arabic below is unaffected.',
  },
  lines: {
    key: 'root-entry-lines',
    get: getRootEntryLines,
    failed: "Couldn't line the English up",
    fallback: 'The backend may have stopped since this page was opened.',
    after: ' The Together view above still shows the whole entry.',
  },
}

/** The ways to read the rest of the entry; the first is the default. */
const VIEWS = ['together', 'lines', 'one']

export default function RootMeaningCard({ root: asked, hasAlternates, accent }) {
  const { rootMeaningStatus, healthFailed, retryHealth } = useHealth()

  const installed = rootMeaningStatus === READY

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['root-meaning', asked],
    queryFn: () => getRootMeaning(asked),
    // Nothing to ask when the book is not on this machine: the message below
    // already says so, and a request would only come back as an empty answer.
    enabled: installed && Boolean(asked),
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
          // Keyed by the root asked about: whether the rest was opened is a
          // question about one root, and carried over it fetched the next
          // root's English, a model call nobody asked for.
          key={asked}
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
  // Whether the rest of the entry is open. The English below it is
  // fetched on that alone, so a root looked up and never opened costs nothing.
  const [opened, setOpened] = useState(false)

  // How the panel reads: the book whole with its English after it, one flowing
  // page with the English of the line you touch, or one line at a time.
  // Together is the default because it is the book as printed; the pairings
  // are a convenience. Remembered, so a reader who prefers one keeps it.
  const [view, setView] = useRemembered('dict.entry-view', VIEWS, 'together')
  const paired = view !== 'together'

  // Asked and got no answer at all. Say so, rather than showing a loading bar
  // that never ends because nothing is still on its way.
  if (healthFailed) {
    return (
      <ErrorAlert title="Couldn't reach the backend" onRetry={onRetryHealth}>
        Nothing can be said about <Letters value={asked} /> until the backend answers.
        This is not a statement about the root or about the book.
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
      <ErrorAlert
        title="Classical lookup failed"
        error={error}
        fallback="The backend may have stopped since this page was opened."
        onRetry={onRetry}
      />
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

  // rest: the entry after its origin sense, cut by the backend
  // (services/root_gloss.rest_of), the same cut its line-by-line English pairs.
  const { core_meaning, sarf_pattern, variances, rest, english } = data.meaning

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
        {/* The sense itself sometimes ends on a line of verse the book cites,
            so it is laid out line by line for the same reason the rest is. */}
        <div className="space-y-1">
          <Lines text={core_meaning} style={{ color: accent }} />
        </div>
      </div>

      {/* The English sits under its own badge, not the card's. The Arabic above
          was typed by a person; this was read off a photograph of the page by a
          machine, and one badge covering both would lend the weaker the standing
          of the stronger. */}
      {english && (
        <div className="space-y-1.5">
          <p className="type-body text-[var(--text-dim)] max-w-prose">{english}</p>
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
          <ol className="space-y-1" dir="rtl">
            {variances.map((v, i) => (
              <li key={i}>
                <span className="type-small text-[var(--text-faint)] me-2">{i + 1}.</span>
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

          The English, and the view toggle (Together, Line by line, One at a
          time), arrive on that press.
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
                { id: 'one', label: 'One at a time' },
              ]}
              value={view}
              onChange={setView}
            />
          )}

          {opened && paired ? (
            <EntryEnglish view={view} root={data.root} accent={accent} />
          ) : (
            <ShowRest lines={config['root-meaning']['rest-lines']} accent={accent} onOpen={() => setOpened(true)}>
              {/* The book first, its English under it. This panel is the
                  book's own words; the English is what a machine made of them,
                  and printing the machine first put a retelling where the
                  reader came looking for the text. */}
              <Lines text={rest} />
            </ShowRest>
          )}

          {opened && !paired && <EntryEnglish view="together" root={data.root} />}
        </div>
      )}

    </div>
  )
}

/**
 * The rest of the entry in English, fetched when the reader opens it.
 *
 * Together: the entry retold as prose under the Arabic. Lines and one: one English
 * line for each Arabic line; the backend does the pairing and refuses an answer it
 * could not line up, so every English line belongs to the Arabic above it.
 * Either carries its own badge saying a machine wrote it, and never replaces
 * the Arabic beside it.
 */
function EntryEnglish({ view, root, accent }) {
  // 'lines' and 'one' are two ways to read the same pairs: one entry, one query.
  const english = ENGLISH[view === 'one' ? 'lines' : view]
  const { data, isFetching, isError, error, refetch } = useQuery({
    queryKey: [english.key, root],
    queryFn: () => english.get(root),
    retry: false,
  })

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
      <ErrorAlert title={english.failed} error={error} fallback={english.fallback} onRetry={refetch}>
        {english.after}
      </ErrorAlert>
    )
  }

  if (!(data?.english || data?.lines?.length)) return null

  return (
    <div className="space-y-1.5">
      {/* The longest entries run past what the model is handed. Saying so is the
          difference between a short retelling and a retelling that stops. */}
      {data.truncated && (
        <p className="type-small text-[var(--text-faint)]">
          The entry was longer than could be read at once, so this covers its opening.
        </p>
      )}
      {view === 'lines' && <LinePage lines={data.lines} accent={accent} />}
      {view === 'one' && <LineSpotlight lines={data.lines} accent={accent} />}
      {view === 'together' && (
        <p className="type-body text-[var(--text-dim)] max-w-prose whitespace-pre-line">
          {data.english}
        </p>
      )}
      <SourceBadge source={data.source} className="ms-auto flex" />
    </div>
  )
}

/** Explanatory prose. Body text, so it keeps the reading size the panels use. */
const Note = ({ children }) => <p className="type-body text-[var(--text-dim)]">{children}</p>

/** The exact letters searched, shown so a spelling mismatch is visible, not guessed at. */
const Letters = ({ value }) => <ArabicText size="sm" className="text-[var(--text)]">{value}</ArabicText>
