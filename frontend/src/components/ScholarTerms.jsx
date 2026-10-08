/**
 * The sorts of ruling classical books give of a hadith, each with one plain line of what it means, and the hadith
 * carrying the chosen one, a page at a time. The chips are the filter. A tap on a hadith opens it as search results do.
 * The kinds, their words and their counts are the server's own (usul.json); a hadith is matched to its book's
 * entry by wording and narrators, so none of this claims more than "possible".
 */
import { useState } from 'react'
import { useInfiniteQuery, useQuery } from '@tanstack/react-query'

import { usulTermQuery, usulTermsQuery } from '../api'
import { useHadithCollections } from '../lib/useHadithCollections'

import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import { AnalyzerSkeleton } from './ui/Skeleton'

function TermHadith({ kind, accent, onOpen }) {
  const { of } = useHadithCollections()
  const { data, isPending, isError, error, refetch, hasNextPage, fetchNextPage, isFetchingNextPage } = useInfiniteQuery(usulTermQuery(kind))
  const items = data?.pages.flatMap((p) => p.items) ?? []
  const total = data?.pages[0].total ?? 0

  return (
    <div className="space-y-3">
      {isPending && <AnalyzerSkeleton />}
      {isError && <ErrorAlert title="Could not load these hadith" error={error} fallback="The hadith could not be reached." onRetry={refetch} />}
      {items.length > 0 && (
        <>
          <ChipRow>
            {items.map((h) => (
              <Chip key={`${h.collection}:${h.number}${h.part}`} accent={accent} onClick={() => onOpen(h)}>
                {of(h.collection).short} {h.number}{h.part}
              </Chip>
            ))}
          </ChipRow>
          {hasNextPage && (
            <button
              type="button"
              disabled={isFetchingNextPage}
              onClick={() => fetchNextPage()}
              className="press type-ui text-[var(--text-dim)] hover:text-[var(--text)] transition-colors"
            >
              {isFetchingNextPage ? 'Loading...' : `Show more (${total - items.length} left)`}
            </button>
          )}
        </>
      )}
    </div>
  )
}

export default function ScholarTerms({ accent, onOpen }) {
  const { data: terms, isPending, isError, error, refetch } = useQuery(usulTermsQuery)
  const [picked, setPicked] = useState(null)
  const term = terms?.find((t) => t.kind === picked) ?? terms?.[0]

  return (
    <div className="space-y-3">
      {isPending && <AnalyzerSkeleton />}
      {isError && <ErrorAlert title="Could not load the scholars' rulings" error={error} fallback="The rulings could not be reached." onRetry={refetch} />}
      {terms && !terms.length && <EmptyState>No rulings are built yet.</EmptyState>}
      {term && (
        <>
          <ChipRow>
            {terms.map((t) => (
              <Chip key={t.kind} selected={t.kind === term.kind} accent={accent} onClick={() => setPicked(t.kind)}>
                {t.label} {t.count}
              </Chip>
            ))}
          </ChipRow>
          <p className="type-ui m-0 text-[var(--text-dim)]">{term.say}</p>
          <TermHadith key={term.kind} kind={term.kind} accent={accent} onOpen={onOpen} />
        </>
      )}
    </div>
  )
}
