/**
 * One collection's books (chapters), to pick which one to read. Each tile: number, picture, English name,
 * and under it the count with the book's own Arabic name faint at the far edge (on its own line when long).
 */
import { useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { hadithBookQuery, hadithBooksQuery } from '../../api'
import { themeVariable } from '../../theme'
import { onHover, warm } from '../../lib/warm'
import { topicOf } from '../../lib/hadithGrade'
import { useOpenAtTop } from '../../lib/scrollToEl'

import ArabicText from '../ui/ArabicText'
import ErrorAlert from '../ui/ErrorAlert'
import EmptyState from '../ui/EmptyState'
import TopicIcon from '../ui/TopicIcon'
import { AnalyzerSkeleton } from '../ui/Skeleton'

const STAGGER_CAP = Number(themeVariable('--hadith-stagger-cap')) || 8

export default function HadithBookList({ collection, onPick, accent }) {
  const { data, isPending, isError, error, refetch } = useQuery(hadithBooksQuery(collection))
  useOpenAtTop()
  const client = useQueryClient()
  const first = data?.[0]?.number
  useEffect(() => {
    if (first != null) warm(client, hadithBookQuery(collection, first))
  }, [client, collection, first])

  if (isPending) return <AnalyzerSkeleton />

  if (isError) {
    return (
      <ErrorAlert title="Could not load the books" error={error} fallback="The books could not be reached." onRetry={refetch} />
    )
  }

  if (!data.length) return <EmptyState>This collection has no books yet.</EmptyState>

  return (
    <ul className="m-0 p-0 list-none grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {data.map((book, i) => (
        <li key={book.number} className="rise-in" style={{ '--i': Math.min(i, STAGGER_CAP) }}>
          <button
            type="button"
            onClick={() => onPick(book.number)}
            {...onHover(client, hadithBookQuery(collection, book.number))}
            style={{ '--c': accent }}
            className="lift press group w-full h-full text-start px-4 py-3 flex items-center gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] hover:border-[var(--c)] transition-colors"
          >
            <span className="type-figure font-medium tabular-nums min-w-[2ch] text-[var(--text-faint)] group-hover:text-[var(--c)] transition-colors">
              {book.number}
            </span>
            <TopicIcon topic={topicOf(book.name)} className="text-[var(--text-faint)] group-hover:text-[var(--c)] transition-colors" />
            <span className="flex-1 min-w-0 type-ui text-[var(--text)] leading-snug">
              {book.name}
              <span className="flex flex-wrap items-baseline gap-x-3 type-small text-[var(--text-faint)]">
                <span className="tabular-nums">{book.count} hadiths</span>
                {/* ml, not ms: the Arabic is right-to-left, so its own start is its right */}
                {book.arabic && <ArabicText size="sm" className="ml-auto">{book.arabic}</ArabicText>}
              </span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}
