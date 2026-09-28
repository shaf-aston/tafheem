/**
 * One collection's books (chapters), to pick which one to read.
 */
import { useQuery } from '@tanstack/react-query'

import { getHadithBooks } from '../api'
import { smartError } from '../lib/apiError'

import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import EmptyState from './ui/EmptyState'
import { AnalyzerSkeleton } from './ui/Skeleton'

export default function HadithBookList({ collection, onPick, accent }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['hadith-books', collection],
    queryFn: () => getHadithBooks(collection),
    staleTime: Infinity,
  })

  if (isPending) return <AnalyzerSkeleton />

  if (isError) {
    return (
      <ErrorAlert title="Could not load the books">
        {smartError(error, 'The books could not be reached.')}
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }

  if (!data.length) return <EmptyState>This collection has no books yet.</EmptyState>

  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {data.map((book) => (
        <li key={book.number}>
          <button
            type="button"
            onClick={() => onPick(book.number)}
            style={{ '--c': accent }}
            className="w-full text-start px-3 py-2.5 rounded-[var(--radius-md)] border border-[var(--border)]
              bg-[var(--surface)] hover:border-[var(--c)] transition-colors
              flex items-baseline justify-between gap-3"
          >
            <span className="text-sm text-[var(--text)]">{book.number}. {book.name}</span>
            <span className="type-small text-[var(--text-faint)] tabular-nums shrink-0">{book.count}</span>
          </button>
        </li>
      ))}
    </ul>
  )
}
