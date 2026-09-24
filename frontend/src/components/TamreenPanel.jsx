/**
 * The teacher's Tamreen exercises: drilled one at a time, or browsed by
 * grammar point. This file only fetches the library and switches between the
 * two; both modes are the components that already exist.
 */
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getTamreen } from '../api'
import { smartError } from '../lib/apiError'
import { readViewParam, writeViewParams } from '../lib/tabUrl'
import { useRemembered } from '../lib/useRemembered'

import Segmented from './ui/Segmented'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import EmptyState from './ui/EmptyState'
import { AnalyzerSkeleton } from './ui/Skeleton'
import TamreenPractise from './TamreenPractise'
import TamreenBrowse from './TamreenBrowse'

const MODES = [
  { id: 'practise', label: 'Practise' },
  { id: 'browse', label: 'Browse by topic' },
]
const MODE_IDS = MODES.map((m) => m.id)

export default function TamreenPanel({ accent, onProgress, onNotes }) {
  const [remembered, remember] = useRemembered('tamreen-mode', MODE_IDS)
  const [mode, setModeNow] = useState(() => readViewParam('mode', MODE_IDS) ?? remembered)
  const setMode = (id) => { setModeNow(id); remember(id) }
  useEffect(() => { writeViewParams({ mode }) }, [mode])

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['tamreen'],
    queryFn: getTamreen,
    staleTime: Infinity,
  })

  if (isPending) return <AnalyzerSkeleton />

  if (isError) {
    return (
      <ErrorAlert title="Could not load the exercises">
        {smartError(error, 'The Tamreen library could not be reached.')}
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }

  if (!data.exercises.length) return <EmptyState>No exercises are filed yet.</EmptyState>

  return (
    <div className="space-y-3">
      <Segmented value={mode} onChange={setMode} accent={accent} options={MODES} className="w-fit" />
      {mode === 'practise'
        ? <TamreenPractise exercises={data.exercises} tags={data.tags} accent={accent} onProgress={onProgress} onNotes={onNotes} />
        : <TamreenBrowse exercises={data.exercises} tags={data.tags} coverage={data.coverage} accent={accent} />}
    </div>
  )
}
