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
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { getRootEntryEnglish, getRootEntryLines, getRootMeaning } from '../../api'
import config from '../../dictionary.json'
import { BROKEN, MISSING, READY } from '../../lib/loadStatus'
import { useHealth } from '../../lib/useHealth'
import { useRemembered } from '../../lib/useRemembered'

import { Lines } from './EntryArabic'
import { LinePage, LineSpotlight } from './EntryLines'
import ArabicText from '../ui/ArabicText'
import ShowRest from '../ui/ShowRest'
import ErrorAlert from '../ui/ErrorAlert'
import Segmented from '../ui/Segmented'
import SmallButton from '../ui/SmallButton'
import { Skeleton } from '../ui/Skeleton'
import SourceBadge from '../ui/SourceBadge'

/** Said when the backend stops answering mid-visit. */
const STOPPED = 'The backend may have stopped since this page was opened.'

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
    fallback: STOPPED,
    after: ' The Together view above still shows the whole entry.',
  },
}

/** One shape of the English as a query, shared by the fetch and the prefetch. */
const englishQuery = (english, root) => ({
  queryKey: [english.key, root],
  queryFn: () => english.get(root),
  retry: false,
})

/** The ways to read the rest of the entry; the first is the default. */
const VIEWS = [
  { id: 'together', label: 'Together' },
  { id: 'lines', label: 'Line by line' },
  { id: 'one', label: 'One at a time' },
]

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
    <section className="p-4 space-y-3" aria-label="Classical root sense">
      {/* The badge is the book's name here, as on every book under it: the
          badge names the source, so a heading saying the same two lines above
          it was the book's name printed twice. Until it arrives the heading
          stands in, so the block is never nameless. */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        {data?.source
          ? <SourceBadge source={data.source} />
          : <h4 className="type-body font-medium text-[var(--text)]">Maqayees al-Lugha</h4>}
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
  // Whether the Arabic of the rest is shown whole. Held here, not in ShowRest:
  // the paired views take ShowRest off the page, and coming back to Together
  // folded the Arabic away again.
  const [whole, setWhole] = useState(false)
  const queryClient = useQueryClient()
  // Both shapes are asked for on the press that opens the rest, not on the
  // press that switches view: fetched on the switch, every first change of
  // view sat on a loading bar.
  const open = () => {
    setOpened(true)
    for (const english of Object.values(ENGLISH)) queryClient.prefetchQuery(englishQuery(english, data.root))
  }

  // How the panel reads: the book whole with its English after it, one flowing
  // page with the English of the line you touch, or one line at a time.
  // Together is the default because it is the book as printed; the pairings
  // are a convenience. Remembered, so a reader who prefers one keeps it.
  const [view, setView] = useRemembered('dict.entry-view', VIEWS.map((v) => v.id))
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
        fallback={STOPPED}
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
        <MachineEnglish source={data.english_source}>
          <p className="type-body text-[var(--text-dim)]">{english}</p>
        </MachineEnglish>
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
              compact
              options={VIEWS}
              value={view}
              onChange={setView}
            />
          )}

          {/* Paired views carry the Arabic in their own lines; Together keeps it here.
              The English is its own press, beside Show all rather than behind
              it: a rest short enough to need no cut had no button at all, and
              its English and its views were out of reach. */}
          {!(opened && paired) && (
            <ShowRest
              lines={config['root-meaning']['rest-lines']}
              accent={accent}
              onOpen={open}
              open={whole}
              onOpenChange={setWhole}
              beside={!opened && <SmallButton onClick={open}>Read in English</SmallButton>}
            >
              {/* The book first, its English under it. This panel is the
                  book's own words; the English is what a machine made of them,
                  and printing the machine first put a retelling where the
                  reader came looking for the text. */}
              <Lines text={rest} />
            </ShowRest>
          )}

          {opened && <EntryEnglish view={view} root={data.root} accent={accent} />}
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
  const { data, isPending, isError, error, refetch } = useQuery(englishQuery(english, root))

  // Said in words, not only drawn: a root whose English is not kept is put into
  // English while the reader waits, a few seconds, and two grey bars alone read
  // as a page that has stuck.
  if (isPending) {
    return (
      <div className="space-y-2" role="status">
        <p className="type-small text-[var(--text-faint)]">Putting the entry into English…</p>
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
    <MachineEnglish source={data.source}>
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
        <p className="type-body text-[var(--text)] whitespace-pre-line">
          {data.english}
        </p>
      )}
    </MachineEnglish>
  )
}

/**
 * English a machine made, with the badge that says so. The badge is pushed to
 * the edge the card's own badge sits on, so the two read as one column of
 * sources rather than one label adrift in the middle of the card.
 */
const MachineEnglish = ({ source, children }) => (
  <div className="space-y-1.5">
    {children}
    <SourceBadge source={source} className="ms-auto flex" />
  </div>
)

/** Explanatory prose. Body text, so it keeps the reading size the panels use. */
const Note = ({ children }) => <p className="type-body text-[var(--text-dim)]">{children}</p>

/** The exact letters searched, shown so a spelling mismatch is visible, not guessed at. */
const Letters = ({ value }) => <ArabicText size="sm" className="text-[var(--text)]">{value}</ArabicText>
