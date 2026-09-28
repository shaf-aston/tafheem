/**
 * One book's hadiths in full, Arabic and English, each with a star.
 */
import { useQuery } from '@tanstack/react-query'

import { getHadithBook } from '../api'
import { smartError } from '../lib/apiError'
import { useHadithFavorites } from '../lib/useHadithFavorites'

import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import EmptyState from './ui/EmptyState'
import FavoriteStar from './ui/FavoriteStar'
import { AnalyzerSkeleton } from './ui/Skeleton'
import HadithText from './ui/HadithText'

export default function HadithList({ collection, book, onBack, accent }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['hadith-book', collection, book],
    queryFn: () => getHadithBook(collection, book),
    staleTime: Infinity,
  })
  const { isFavorite, toggle } = useHadithFavorites()

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={onBack}
        className="type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors"
      >
        &larr; Books
      </button>

      {isPending && <AnalyzerSkeleton />}

      {isError && (
        <ErrorAlert title="Could not load this book">
          {smartError(error, 'The hadiths could not be reached.')}
          <RetryButton onClick={refetch} />
        </ErrorAlert>
      )}

      {data && (
        <>
          <h3 className="text-sm font-medium text-[var(--text)]">{data.book.number}. {data.book.name}</h3>

          {data.hadiths.length === 0 ? (
            <EmptyState>This book has no hadiths yet.</EmptyState>
          ) : (
            <ul className="list-none m-0 p-0 space-y-2">
              {data.hadiths.map((h) => (
                <HadithText
                  key={`${h.number}${h.part}`}
                  label={`${h.number}${h.part}`}
                  arabic={h.arabic}
                  english={h.english}
                  accent={accent}
                  action={<FavoriteStar on={isFavorite(h)} onClick={() => toggle(h)} />}
                />
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  )
}
