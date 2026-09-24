/**
 * Daleel: find the passage that says it, in the books themselves.
 *
 * One box, asked in Arabic or in English, searched across every installed book
 * at once. It quotes; it does not rule. Every hit carries the book it came
 * from, where in that book it sits, and how the match was made, because a
 * passage without its place is an assertion rather than evidence.
 *
 * Which books are searched is a filter on the answer, not a different
 * question: narrowing re-asks the same question straight away rather than
 * leaving passages on screen from books the reader has just excluded.
 */
import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { findDaleel, getDaleelBooks } from '../api'
import { smartError } from '../lib/apiError'
import { isArabic, mostlyArabic } from '../lib/arabicText'
import { plainEntry } from '../lib/laneEntry'
import { sourcesFor, useSources } from '../lib/useSources'
import { useArrival, useHeld } from '../lib/useArrival'
import { useHistory } from '../lib/useHistory'
import { LANE, LANE_TIDY_LABEL, LANE_TIDY_TITLE, useLaneTidy } from '../lib/useLaneTidy'

import ArabicText from './ui/ArabicText'
import BookPicker from './ui/BookPicker'
import EmptyState from './ui/EmptyState'
import FlagButton from './ui/FlagButton'
import MicButton from './ui/MicButton'
import PlaceLinks from './ui/PlaceLinks'
import ErrorAlert from './ui/ErrorAlert'
import RecentRow from './ui/RecentRow'
import RetryButton from './ui/RetryButton'
import { GoButton } from './ui/RootActions'
import SearchBox from './ui/SearchBox'
import SectionHeader from './ui/SectionHeader'
import ShowRest from './ui/ShowRest'
import { AnalyzerSkeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'

/**
 * How a hit was made, said in the reader's words beside it.
 *
 * An exact hit says nothing: it is what was asked for. The other three are the
 * search quietly widening the question, and a reader who typed one word and is
 * shown another needs to be told which liberty was taken.
 */
const MATCH_NOTE = {
  loose: 'close spelling',
  root: 'same root',
  related: 'related word',
}

export default function DaleelPanel({ accent, incoming, arrival, onGo, onVisit }) {
  const [laneTidy, setLaneTidy] = useLaneTidy()
  const [query, setQuery] = useState(incoming ?? '')
  const [chosen, setChosen] = useState([])

  const { history, push: remember } = useHistory('daleel-history')

  // A question that came back is a place reached: Recent, the trail, and the
  // address bar all record it. Which books were searched is not in it; that is
  // a filter on the answer, not a different question. See lib/journey.js.
  const mutation = useMutation({
    mutationFn: findDaleel,
    onSuccess: (_, { q }) => { remember({ q }); onVisit?.(q) },
  })

  // The list of books to offer. Asked for once and kept: it changes only when
  // the index is rebuilt, which cannot happen while the page is open.
  const { data: catalogue = [] } = useQuery({
    queryKey: ['daleel-books'],
    queryFn: getDaleelBooks,
    staleTime: Infinity,
  })

  // A question arriving: handed over from another tab, or the back arrow
  // returning to one. App no longer remounts the panel for it, that remount
  // faded the whole page back in and read as a flash (see lib/useArrival), so
  // the box follows the question here, during the render.
  const { arrived, returning } = useArrival(arrival, mutation.isPending)
  if (arrived && incoming) setQuery(incoming)

  // And it is asked again, so an arrival ends in an answer.
  const { mutate: ask } = mutation
  useEffect(() => {
    if (incoming) ask({ q: incoming, books: [] })
  }, [arrival, incoming, ask])

  const submit = (overrideQuery, overrideBooks) => {
    const q = (overrideQuery ?? query).trim()
    if (!q) return
    // No language is sent: one request reads the Arabic and the English index
    // together, which is what makes the single box honest.
    mutation.mutate({ q, books: overrideBooks ?? chosen })
  }

  // Changing which books are searched re-asks the same question straight away.
  // Leaving the old results on screen under a new filter would show passages
  // from books the reader had just excluded, which is the one thing this
  // control must never do. The books are passed rather than read back, because
  // the state has not settled by the time this runs.
  const narrow = (books) => {
    setChosen(books)
    if (mutation.data || mutation.isError) submit(undefined, books)
  }

  // The books come in one order every time, taken from sources.json rather
  // than from how well this particular search happened to go. A page whose
  // sections move around between searches cannot be learned.
  const { sources } = useSources()
  // Stale results under a spinner is a state a reader has no way to name; the
  // skeleton fully replaces them instead of sitting on top. A return is the one
  // exception: nothing new was asked for, so the passages already read stay up
  // until the same ones come back. See lib/useArrival.
  const data = useHeld(mutation.isPending ? undefined : mutation.data, returning)
  const books = groupByBook(data?.hits ?? [], sourcesFor(sources, 'daleel'))
  const passageCount = data?.hits?.length ?? 0
  const bookCount = books.length

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Daleel"
        arabic="دليل"
        subtitle="Searchable in Arabic or in English. It quotes the books; it does not rule."
      />

      {/* Every recent question, whichever language it was asked in, each chip
          set in its own script. They used to be split into two lists by the
          toggle above, so half of them were hidden at any one time. */}
      <RecentRow
        items={history.map((h) => h.q)}
        accent={accent}
        onPick={(q) => { setQuery(q); submit(q) }}
      />

      <div className="space-y-3">
        {/* The same field as the Dictionary and the Quran tabs, down to the
            keycap and the microphone: three tabs that take a question should
            not take it three different ways. See ui/SearchBox. */}
        <SearchBox
          id="daleel-input"
          label="Arabic or English"
          hint="Enter to search, or say it"
          placeholder="Search الصبر or patience"
          value={query}
          onChange={setQuery}
          onSubmit={submit}
          onClear={() => { setQuery(''); mutation.reset() }}
          busy={mutation.isPending}
          accent={accent}
        >
          {/* Speaking a phrase, not an ayah: Daleel searches whatever words come
              back, so it asks only for those and never for a list of ayahs. */}
          <MicButton
            onHeard={({ text }) => { setQuery(text || ''); mutation.reset() }}
            accent={accent}
            title="Say what you are looking for"
          />
        </SearchBox>

        {/* Below the search box, not above: most searches want the whole
            library, so the box that everyone uses leads and the filter, which
            is the occasional case, folds under it. See ui/BookPicker. */}
        <BookPicker
          books={catalogue}
          onChange={narrow}
          accent={accent}
          sourceLabel={(key) => sources.find((s) => s.key === key)?.label ?? key}
        />
      </div>

      <PlaceLinks query={query} onGo={onGo} accent={accent} />

      {mutation.isError && (
        <ErrorAlert title="Search failed">
          {smartError(mutation.error, 'Could not reach the backend.')}
          <RetryButton onClick={() => submit()} />
        </ErrorAlert>
      )}

      {/* Not an EmptyState: an index that was never built is a thing that could
          not run, and EmptyState is only for a search that ran and found
          nothing. Saying "nothing matches" here would blame the question for a
          missing file, so it says what is wrong and how to put it right. */}
      {data?.ready === false && (
        <ErrorAlert title="Search index not built">
          The books have not been indexed on this machine, so every search would
          come back empty. Build it with{' '}
          <code className="px-1 rounded bg-[var(--surface-hi)] text-[var(--text)]">
            python backend/scripts/build_daleel_index.py
          </code>
        </ErrorAlert>
      )}

      {/* With a filter on, the sentence has to name the limit. "Nothing in the
          books" while nine books out of ten were excluded is a claim about the
          whole library that the search never made. */}
      {data?.ready !== false && data && data.hits.length === 0 && (
        <EmptyState>
          {data.books?.length
            ? `Nothing in ${data.books.length === 1 ? 'that book' : 'those books'}`
              + ` matches “${data.query}”.`
              + ' The rest of the library has not been searched.'
            : `Nothing in the books matches “${data.query}”.`}
        </EmptyState>
      )}

      {/* The live region is this one sentence, not the whole results block: with
          the block itself announced, every passage in it got read aloud. */}
      <p className="sr-only" role="status" aria-live="polite">
        {data ? `${passageCount} passages in ${bookCount} books` : ''}
      </p>

      {mutation.isPending && !data && <AnalyzerSkeleton />}

      <div className="space-y-5">
      {books.map(([label, hits]) => {
        const isLane = label === LANE
        return (
        <section key={label} className="space-y-3">
          <div className="flex items-center gap-3">
            <SourceBadge source={hits[0].source} />
            <span className="type-small text-[var(--text-faint)] tabular-nums">
              {hits.length}
            </span>
            {/* Only Lane carries the scholar's marks, so only his row has the switch. */}
            {isLane && (
              <div className="ms-auto">
                <FlagButton value={laneTidy} onChange={setLaneTidy} accent={accent} title={LANE_TIDY_TITLE}>
                  {LANE_TIDY_LABEL}
                </FlagButton>
              </div>
            )}
          </div>

          <ul className="space-y-3">
            {hits.map((hit) => (
              <li key={`${label}-${hit.locator}`}>
                <Quotation hit={hit} onGo={onGo} accent={accent} tidy={isLane && laneTidy} />
              </li>
            ))}
          </ul>
        </section>
        )
      })}
      </div>
    </div>
  )
}

/**
 * One passage, exactly as its book has it.
 *
 * The Arabic is first and large because it is the thing that was asked for.
 * The address sits quietly at the foot: a quotation with no address is a
 * rumour, but it is not what the eye should land on first.
 */
function Quotation({ hit, onGo, accent, tidy }) {
  const note = MATCH_NOTE[hit.match]

  return (
    <article
      // The accent is set here, not inherited: it was read off the search box,
      // which is a different subtree, so the hover below resolved to nothing.
      style={{ '--c': accent }}
      className="rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
        p-5 space-y-3"
    >
      {hit.arabic && <Passage text={hit.arabic} accent={accent} tidy={tidy} arabic />}

      {hit.english && <Passage text={hit.english} accent={accent} tidy={tidy} />}

      <div className="flex items-center justify-between gap-3 flex-wrap pt-1">
        {/* A dictionary entry is cited by the word itself, which is already the
            quotation above. Printing it again in a mono face said nothing and
            set the same Arabic twice in two different types. */}
        <Locator text={hit.locator === hit.arabic ? '' : hit.locator} />

        <div className="flex items-center gap-3">
          {/* Set apart from the quiet metadata beside it. This is the one line
              that stops a probable typo-fix from reading as a clean find, and
              in the same grey as the citation it was indistinguishable from
              filler. */}
          {note && (
            <span
              className="type-small px-2 py-0.5 rounded-full border"
              style={{
                color: 'var(--warn)',
                borderColor: 'color-mix(in srgb, var(--warn) 35%, transparent)',
              }}
            >
              {note}
            </span>
          )}
          {onGo && isAyah(hit.locator) && (
            <GoButton onClick={() => onGo('quran', hit.locator)} style={{ '--c': accent }}>
              Open the ayah
            </GoButton>
          )}
        </div>
      </div>
    </article>
  )
}

/**
 * One side of a passage, cut to a few lines when it runs long.
 *
 * Ibn Kathir's entries are whole pages, and set beside an ayah of six words
 * they turned the results into one card and a wall. The cut is not a
 * shortening: the whole passage is a press away, and no card is allowed to
 * decide the height of the page on its own.
 *
 * Both sides fold, not only the English. Every Arabic text Daleel held was
 * short, so the wall could only ever come from a translation; the unabridged
 * Arabic commentaries average a printed page each and put the same wall in the
 * language the reader asked in.
 *
 * ui/ShowRest measures the overflow rather than counting characters, so a
 * passage that happens to fit grows no button. The character threshold this
 * used to keep called a 330-character line long on a phone and on a desktop
 * alike, where it is four lines and one.
 */
function Passage({ text, accent, tidy = false, arabic = false }) {
  // A dictionary entry arrives with the marks its own dump wrote into it.
  // Every other book passes through untouched, none of them carrying those
  // marks in the first place.
  const said = plainEntry(text, { tidy })

  return (
    <ShowRest lines={4} accent={accent}>
      {arabic && mostlyArabic(said) ? (
        <ArabicText size="lg" className="block leading-loose whitespace-pre-line">{said}</ArabicText>
      ) : (
        <p className="text-sm text-[var(--text-dim)] leading-relaxed whitespace-pre-line">
          {said}
        </p>
      )}
    </ShowRest>
  )
}

/**
 * Hits grouped by book, books in the order sources.json lists them.
 *
 * The order is fixed rather than by how well each book scored, because the two
 * differ and the fixed one is the useful one. On a misspelling every book can
 * match about equally well, and ordering by score put a dictionary idiom above
 * al-Fatihah purely because it was the shorter line.
 */
function groupByBook(hits, order) {
  const books = new Map()
  for (const hit of hits) {
    const key = hit.source?.key ?? 'unknown'
    if (!books.has(key)) books.set(key, [])
    books.get(key).push(hit)
  }

  const rank = new Map(order.map((source, n) => [source.key, n]))
  return [...books.entries()].sort(
    ([a], [b]) => (rank.get(a) ?? 99) - (rank.get(b) ?? 99),
  )
}

/** "2:255" is somewhere the Quran tab can open; "§1.4.4" and a root are not. */
const isAyah = (locator) => /^\d+:\d+$/.test(locator)

/**
 * Where a passage came from. An ayah reference like 2:45 is a number and reads
 * well in the mono face; a book citation is Arabic, and the mono face has no
 * Arabic in it, so the browser substituted letter by letter and the word came
 * out unjoined. Arabic also has to be marked rtl or a page number lands on the
 * wrong side of its ص.
 */
function Locator({ text }) {
  if (!text) return <span />
  if (isArabic(text)) {
    return (
      <ArabicText size="tiny" className="arabic-inline text-[var(--text-faint)]">
        {text}
      </ArabicText>
    )
  }
  return <span className="type-small text-[var(--text-faint)] font-mono">{text}</span>
}
