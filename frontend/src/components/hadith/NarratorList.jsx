/**
 * Every narrator named in our hadith, the most narrated first, a page at a time.
 * A tap opens his page. Generations are the server's own groups (rijal.json).
 */
import { useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'

import { narratorListQuery } from '../../api'
import { useOpenAtTop } from '../../lib/scrollToEl'

import ArabicText from '../ui/ArabicText'
import Chip from '../ui/Chip'
import ChipRow from '../ui/ChipRow'
import EmptyState from '../ui/EmptyState'
import { NarratorWhen } from './NarratorParts'
import ErrorAlert from '../ui/ErrorAlert'
import { AnalyzerSkeleton } from '../ui/Skeleton'
import LoadMore from '../ui/LoadMore'

export default function NarratorList({ accent, onOpen }) {
  useOpenAtTop()
  const [generation, setGeneration] = useState('')
  const { data, isPending, isError, error, refetch, hasNextPage, fetchNextPage, isFetchingNextPage } = useInfiniteQuery(narratorListQuery(generation))
  const first = data?.pages[0]
  const items = data?.pages.flatMap((p) => p.items) ?? []

  return (
    <div className="space-y-3">
      {first?.generations.length > 0 && (
        <ChipRow>
          <Chip selected={generation === ''} accent={accent} onClick={() => setGeneration('')}>All</Chip>
          {first.generations.map((g) => (
            <Chip key={g.key} selected={generation === g.key} accent={accent} onClick={() => setGeneration(g.key)}>{g.label}</Chip>
          ))}
        </ChipRow>
      )}

      {isPending && <AnalyzerSkeleton />}
      {isError && <ErrorAlert title="Could not load the narrators" error={error} fallback="The narrators could not be reached." onRetry={refetch} />}
      {first && !items.length && <EmptyState>{generation ? 'No narrators of this generation are built yet.' : 'No narrators are built yet.'}</EmptyState>}

      {items.length > 0 && (
        <>
          <ul className="m-0 p-0 list-none grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((n) => (
              <li key={n.id} className="min-w-0">
                <button
                  type="button"
                  onClick={() => onOpen(n.id)}
                  style={{ '--c': accent }}
                  className="lift press w-full h-full text-start px-4 py-3 space-y-1 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] hover:border-[var(--c)] transition-colors"
                >
                  <ArabicText as="span" size="base" className="block">{n.name_ar}</ArabicText>
                  {/* The name in English letters, for a reader who cannot yet read the Arabic. */}
                  {n.name_en && <span className="block type-small text-[var(--text-dim)]">{n.name_en}</span>}
                  <NarratorWhen who={n} also={[`in ${n.hadith_count} of our hadith`]} />
                </button>
              </li>
            ))}
          </ul>
          {hasNextPage && (
            <LoadMore left={first.total - items.length} busy={isFetchingNextPage} onClick={fetchNextPage} />
          )}
        </>
      )}
    </div>
  )
}
