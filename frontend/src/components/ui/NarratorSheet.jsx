/**
 * The pop-up about one narrator of a chain, tapped in a hadith. His name, how
 * sunnah.com grades him, when and where he lived, how many he taught and was
 * taught by, and a way to his full page. A 404 means this machine holds no
 * page for him (rijal.db unbuilt or he was never fetched), said in a line.
 */
import { useQuery } from '@tanstack/react-query'

import { narratorQuery } from '../../api'
import { errorStatus } from '../../lib/apiError'

import BottomSheet from './BottomSheet'
import CloseButton from './CloseButton'
import ErrorAlert from './ErrorAlert'
import { NarratorFacts, NarratorName } from './NarratorParts'
import { Skeleton } from './Skeleton'
import SmallButton from './SmallButton'
import StatusNote from './StatusNote'

export default function NarratorSheet({ id, onClose, onOpenPage }) {
  const { data: who, isPending, isError, error, refetch } = useQuery(narratorQuery(id))

  return (
    <BottomSheet label="Narrator" onClose={onClose} className="max-h-[var(--sheet-tall)] flex flex-col">
      <header className="flex items-start justify-between gap-3 px-5 pt-4 pb-3">
        {who ? <NarratorName who={who} /> : <h2 className="type-ui font-semibold text-[var(--text)]">Narrator</h2>}
        <CloseButton onClick={onClose} className="shrink-0" />
      </header>

      <div className="overflow-y-auto px-5 pb-5 space-y-3">
        {isPending && <Skeleton className="h-24 w-full" />}
        {isError && (errorStatus(error) === 404
          ? <StatusNote>No page for this narrator is built on this machine.</StatusNote>
          : <ErrorAlert title="Could not load the narrator" error={error} fallback="Try again." onRetry={refetch} />)}
        {who && (
          <>
            <NarratorFacts who={who} />
            <SmallButton onClick={() => onOpenPage(id)}>Open full page</SmallButton>
          </>
        )}
      </div>
    </BottomSheet>
  )
}
