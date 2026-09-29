/**
 * One book's hadiths in full. The title bar stays under the app header while
 * you read: the way back, how far through you are, and a jump to a number.
 */
import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getHadithBook } from '../api'
import { smartError } from '../lib/apiError'
import { scrollToEl } from '../lib/scrollToEl'
import { topicOf } from '../lib/hadithGrade'

import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import EmptyState from './ui/EmptyState'
import TopicIcon from './ui/TopicIcon'
import { AnalyzerSkeleton } from './ui/Skeleton'
import HadithCards from './HadithCards'

/** How far down the page you are, drawn into `ref` without re-rendering per scroll. */
function useReadingRail(ref) {
  useEffect(() => {
    const draw = () => {
      const room = document.documentElement.scrollHeight - window.innerHeight
      if (ref.current) ref.current.style.width = `${room > 0 ? Math.min(100, (window.scrollY / room) * 100) : 0}%`
    }
    draw()
    window.addEventListener('scroll', draw, { passive: true })
    return () => window.removeEventListener('scroll', draw)
  }, [ref])
}

export default function HadithList({ collection, collections, book, onBack, accent }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['hadith-book', collection, book],
    queryFn: () => getHadithBook(collection, book),
    staleTime: Infinity,
  })
  const rail = useRef(null)
  useReadingRail(rail)
  const [missing, setMissing] = useState(false)

  const jump = (event) => {
    event.preventDefault()
    const number = new FormData(event.currentTarget).get('number')
    const card = number && document.querySelector(`#hadith-${number}, #hadith-${number}a`)
    setMissing(Boolean(number) && !card)
    scrollToEl(card, 'top')
  }

  return (
    <div className="space-y-3">
      <div className="sticky z-30 top-[var(--app-header-h,0px)] -mx-1 px-1 pt-2 bg-[var(--bg)]">
        <div className="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            onClick={onBack}
            className="press type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors"
          >
            &larr; Books
          </button>
          {data && (
            <h3 className="flex-1 min-w-0 flex items-center gap-2 text-sm font-medium text-[var(--text)]">
              <TopicIcon topic={topicOf(data.book.name)} className="w-4 h-4" />
              {data.book.number}. {data.book.name}
              <span className="ms-2 type-small font-normal text-[var(--text-faint)]">{data.hadiths.length} hadiths</span>
            </h3>
          )}
          <form onSubmit={jump} className="flex items-center gap-2">
            {missing && <span role="status" className="type-small text-[var(--text-faint)]">Not in this book</span>}
            <input
              name="number"
              type="number"
              min="1"
              inputMode="numeric"
              aria-label="Go to hadith number"
              placeholder="Go to #"
              onChange={() => setMissing(false)}
              className="type-small w-24 h-[var(--layout-chip)] px-3 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text)] outline-none focus:border-[var(--c)]"
              style={{ '--c': accent }}
            />
          </form>
        </div>
        <div className="mt-2 h-0.5 rounded-full bg-[var(--border)]">
          <div ref={rail} style={{ background: accent }} className="h-full w-0 rounded-full" />
        </div>
      </div>

      {isPending && <AnalyzerSkeleton />}

      {isError && (
        <ErrorAlert title="Could not load this book">
          {smartError(error, 'The hadiths could not be reached.')}
          <RetryButton onClick={refetch} />
        </ErrorAlert>
      )}

      {data && (data.hadiths.length === 0
        ? <EmptyState>This book has no hadiths yet.</EmptyState>
        : <HadithCards items={data.hadiths} collection={collection} collections={collections} accent={accent} />)}
    </div>
  )
}
