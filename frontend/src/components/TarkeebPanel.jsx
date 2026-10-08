/**
 * The books' own worked tarkeeb, in the drawer at the foot of the Nahw page: the
 * checked diagrams to compare a typed sentence against. The set is small and
 * fixed, so it is fetched once and filtered here.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getTarkeebExamples } from '../api'
import { exampleMatches } from '../lib/exampleSearch'
import { buildIraabExportText } from '../lib/iraabExport'
import { useInView } from '../lib/useInView'
import { useRemembered } from '../lib/useRemembered'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import CopyButton from './ui/CopyButton'
import SearchBox from './ui/SearchBox'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import { GoButton } from './ui/RootActions'
import SourceBadge from './ui/SourceBadge'
import { Skeleton } from './ui/Skeleton'
import TarkeebFigure from './TarkeebFigure'

// Browsed by grammar topic, shared by every book, so a second book teaching kana
// lands under the same chip. The book chips appear only with more than one book.

export default function TarkeebPanel({ accent, onWordByWord }) {
  const [query, setQuery] = useState('')
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['tarkeeb-examples'],
    queryFn: getTarkeebExamples,
  })

  const books = useMemo(() => data?.books ?? [], [data])
  // Which book they filtered to, kept between visits. The empty key is every
  // book, and it heads the allowed list so it is both the choice they can come
  // back to and what an unknown book falls back to. See lib/useRemembered.
  const bookKeys = useMemo(() => ['', ...books.map((one) => one.key)], [books])
  const [bookKey, setBookKey] = useRemembered('tarkeeb-book', bookKeys)
  // Every example, each carrying the book it came from, so one list feeds
  // searching, the topic counts and the cards.
  const all = useMemo(
    () => books.flatMap((one) => one.examples.map((e) => ({ ...e, book: one }))),
    [books],
  )
  const inBook = useMemo(
    () => (bookKey ? all.filter((e) => e.book.key === bookKey) : all),
    [all, bookKey],
  )
  // The topic's own names, for the card that is showing an example of it. The
  // topic itself stays on every example (and in the data file) for querying, 
  // it is just not a filter row on screen any more.
  const named = useMemo(() => new Map((data?.topics ?? []).map((t) => [t.key, t])), [data])
  const shown = useMemo(
    () => inBook.filter((example) => exampleMatches(example, named.get(example.topic), query)),
    [inBook, named, query],
  )

  return (
    <div className="space-y-5">
      {isError && (
        <ErrorAlert title="Could not load the examples" error={error} onRetry={() => refetch()} />
      )}
      {isPending && <Skeleton className="h-40" />}

      {books.length > 0 && (
        <>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            {/* One book is named by its badge beside the count; the line saying
                it too printed the same name twice on one row. */}
            <p className="text-sm text-[var(--text-dim)]">
              {all.length} worked examples
              {books.length > 1 && (
                <>
                  {' '}from <span className="text-[var(--text)]">{books.length} books</span>
                </>
              )}
            </p>
            {books.length === 1 && <SourceBadge source={books[0].source} />}
          </div>

          {books.length > 1 && (
            <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by book">
              <Chip tinted selected={!bookKey} accent={accent} onClick={() => setBookKey('')}>
                Every book <Count>{all.length}</Count>
              </Chip>
              {books.map((one) => (
                <Chip
                  key={one.key}
                  tinted
                  selected={bookKey === one.key}
                  accent={accent}
                  onClick={() => setBookKey(one.key)}
                  title={one.detail}
                >
                  {one.title} <Count>{one.examples.length}</Count>
                </Chip>
              ))}
            </div>
          )}

          <SearchBox
            id="tarkeeb-search"
            label="Find an example"
            placeholder="A word, its meaning, or a topic, e.g. كتاب or “verbal sentence”"
            value={query}
            onChange={setQuery}
            accent={accent}
          />

          {/* Announces filter results as they change, since the count and list
              update from typing alone with no page navigation to cue it. */}
          <div aria-live="polite">
            <p className="type-small text-[var(--text-faint)] mb-2">
              {shown.length} of {inBook.length} examples
            </p>
            {shown.length === 0 ? (
              <EmptyState>
                No example matches that. Try a shorter word.
              </EmptyState>
            ) : (
              <ul className="space-y-4">
                {shown.map((example) => (
                  <li key={example.id}>
                    <Example
                      example={example}
                      topic={named.get(example.topic)}
                      showBook={books.length > 1}
                      accent={accent}
                      onWordByWord={onWordByWord}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  )
}

/** The number of examples behind a chip, quiet enough not to compete with its name. */
const Count = ({ children }) => (
  <span className="opacity-60 tabular-nums">{children}</span>
)

function Example({ example, topic, showBook, accent, onWordByWord }) {
  // A diagram is the expensive part of a card and there are dozens of cards.
  // Building them all on open cost a fifth of a second of frozen tab; each one
  // now waits until its card is nearly on screen.
  const [ref, near] = useInView({ margin: '600px' })

  // Laid out as the Analyse page lays out a sentence: the line naming it and the
  // Copy button above, then the same figure card (enlarge, coverage line).
  return (
    <article ref={ref} className="space-y-3">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div
          className="flex items-center gap-2 text-sm px-3 py-2 rounded-[var(--radius-md)]
            bg-[var(--surface)] border border-[var(--border)]"
        >
          <span className="text-[var(--text)]">{example.translation}</span>
          {topic && <ArabicText size="sm" className="text-[var(--text-faint)]">{topic.ar}</ArabicText>}
          {/* The badge already names the book, so the title is not repeated. */}
          {showBook && <SourceBadge source={example.book.source} />}
        </div>
        <CopyButton text={buildIraabExportText({ sentence: example.sentence, words: [], tree: example })} />
      </div>
      {near ? (
        <TarkeebFigure tarkeeb={example} />
      ) : (
        // Holds the card's height so the page does not jump as diagrams arrive.
        <div className="h-32" aria-hidden="true" />
      )}
      {onWordByWord && (
        // Same pill as every other hand-off between tabs, not a bespoke link.
        <GoButton style={{ '--c': accent }} onClick={() => onWordByWord(example.sentence)}>
          Word by word →
        </GoButton>
      )}
    </article>
  )
}
