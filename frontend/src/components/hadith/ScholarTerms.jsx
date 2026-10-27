/**
 * The sorts of ruling classical books give of a hadith, each with one plain line of what it means, and the hadith
 * carrying the chosen one, a page at a time. The chips are the filter. A tap on a hadith opens it as search results do.
 * The kinds, their words and their counts are the server's own (usul.json); a hadith is matched to its book's
 * entry by wording and narrators, so none of this claims more than "possible".
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { usulTermsQuery } from '../../api'
import { useOpenAtTop } from '../../lib/motion/scrollToEl'

import Chip from '../ui/inputs/Chip'
import ChipRow from '../ui/inputs/ChipRow'
import EmptyState from '../ui/feedback/EmptyState'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import { AnalyzerSkeleton } from '../ui/feedback/Skeleton'
import TermHadith from './TermHadith'

export default function ScholarTerms({ accent, onOpen }) {
  useOpenAtTop()
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
