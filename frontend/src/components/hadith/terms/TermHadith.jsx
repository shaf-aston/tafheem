/**
 * The hadith carrying one sort of ruling, a page at a time, as chips that open the hadith. Used by the Scholars
 * list and by a term's card in the Terms view. Where the rulings index is not built (a 404) it says no hadith carry
 * the ruling, rather than showing an error the reader can do nothing about.
 */
import { useInfiniteQuery } from '@tanstack/react-query'

import { usulTermQuery } from '../../../api'
import { useHadithCollections } from '../useHadithCollections'

import Chip from '../../ui/inputs/Chip'
import ChipRow from '../../ui/inputs/ChipRow'
import EmptyState from '../../ui/feedback/EmptyState'
import ErrorAlert from '../../ui/feedback/ErrorAlert'
import { AnalyzerSkeleton } from '../../ui/feedback/Skeleton'
import LoadMore from '../../ui/buttons/LoadMore'

export default function TermHadith({ kind, accent, onOpen }) {
  const { of } = useHadithCollections()
  const { data, isPending, isError, error, refetch, hasNextPage, fetchNextPage, isFetchingNextPage } = useInfiniteQuery(usulTermQuery(kind))
  const items = data?.pages.flatMap((p) => p.items) ?? []
  const unbuilt = error?.response?.status === 404
  const total = data?.pages[0].total ?? 0

  return (
    <div className="space-y-3">
      {isPending && <AnalyzerSkeleton />}
      {isError && !unbuilt && <ErrorAlert title="Could not load these hadith" error={error} fallback="The hadith could not be reached." onRetry={refetch} />}
      {!isPending && (!isError || unbuilt) && !items.length && <EmptyState>No hadith carry this ruling.</EmptyState>}
      {items.length > 0 && (
        <>
          {/* Named and quiet, so these read as hadith to open, not as more rulings to filter by. */}
          <p className="type-tiny text-[var(--text-faint)] m-0 pt-2">{total} hadith with this ruling, tap one to read it</p>
          <ChipRow>
            {items.map((h) => (
              <Chip key={`${h.collection}:${h.number}${h.part}`} quiet accent={accent} onClick={() => onOpen(h)}>
                {of(h.collection).short} {h.number}{h.part}
              </Chip>
            ))}
          </ChipRow>
          {hasNextPage && (
            <LoadMore left={total - items.length} busy={isFetchingNextPage} onClick={fetchNextPage} />
          )}
        </>
      )}
    </div>
  )
}
