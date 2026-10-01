// One quiet line under a phrase that opens it as every other dialect says it.
// Every dialect fills the same spine slots, so the phrase is found by its slot.
// Fetched only once opened, and a whole lesson at a time, so stepping through
// the sheet's phrases costs no further wait.
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { colloquialCompareQuery } from '../../api'
import { useSetting } from '../../lib/settings'
import ArabicText from '../ui/ArabicText'
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'
import { FOCUS } from './Face'
import Spelling from './Spelling'

function Rows({ place, slot }) {
  const { data, isPending, isError, error, refetch } = useQuery(colloquialCompareQuery(place.unit, place.lesson))
  if (isPending) return <Skeleton className="h-24" />
  if (isError) return <ErrorAlert inline title="Other dialects" error={error} fallback="The other dialects could not be reached." onRetry={refetch} />
  return (
    <ul className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] divide-y divide-[var(--border)]">
      {data.dialects.filter((d) => d.key !== place.dialect).map((d) => {
        const said = d.phrases?.find((p) => p.slot === slot)
        return (
          <li key={d.key} className="flex items-baseline justify-between gap-4 px-4 py-2">
            <span className="shrink-0 type-small text-[var(--text-faint)]">{d.label}</span>
            {said
              ? <span className="min-w-0 text-end"><ArabicText as="p" size="sm" className="text-[var(--text)]">{said.arabic}</ArabicText><Spelling className="block">{said.transliteration}</Spelling></span>
              : <span className="type-small text-[var(--text-faint)]">Coming</span>}
          </li>
        )
      })}
    </ul>
  )
}

export default function OtherDialects({ place, slot }) {
  const wanted = useSetting('colloq-other-dialects')
  const [open, setOpen] = useState(false)
  if (!wanted || !place || !slot) return null
  return (
    <div className="space-y-3">
      <button type="button" aria-expanded={open} onClick={() => setOpen(!open)}
        className={`press block mx-auto type-small text-[var(--text-dim)] hover:text-[var(--text)] underline underline-offset-4 rounded ${FOCUS}`}>
        {open ? 'Hide the other dialects' : 'Say it in the other dialects'}
      </button>
      {open && <Rows place={place} slot={slot} />}
    </div>
  )
}
