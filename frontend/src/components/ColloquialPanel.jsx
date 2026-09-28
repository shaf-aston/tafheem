/**
 * Colloquial: spoken Arabic, a dialect at a time.
 *
 * The catalogue (titles only) names the dialects and their units; choosing a
 * unit fetches it whole. The dialect is remembered between visits, and a row of
 * choices appears only where there is more than one to choose, so a tab with a
 * single dialect and unit is just the lessons.
 */
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { getColloquial, getColloquialUnit } from '../api'
import { smartError } from '../lib/apiError'
import { useRemembered } from '../lib/useRemembered'
import UnitView from './colloquial/UnitView'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import { AnalyzerSkeleton } from './ui/Skeleton'

const asOptions = (items, id, label) => items.map((item) => ({ id: item[id], label: item[label] }))

function Failed({ error, onRetry }) {
  return (
    <ErrorAlert title="Could not load the lessons">
      {smartError(error, 'The Colloquial lessons could not be reached.')}
      <RetryButton onClick={onRetry} />
    </ErrorAlert>
  )
}

function Unit({ dialect, unit }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['colloquial-unit', dialect, unit],
    queryFn: () => getColloquialUnit(dialect, unit),
    staleTime: Infinity,
  })
  if (isPending) return <AnalyzerSkeleton />
  if (isError) return <Failed error={error} onRetry={refetch} />
  return <UnitView unit={data} />
}

export default function ColloquialPanel() {
  const catalogue = useQuery({ queryKey: ['colloquial'], queryFn: getColloquial, staleTime: Infinity })
  const dialects = catalogue.data?.dialects ?? []
  const [dialectKey, setDialectKey] = useRemembered('colloq-dialect', dialects.map((d) => d.key))
  const [unitKey, setUnitKey] = useState(null)

  const dialect = dialects.find((d) => d.key === dialectKey)
  const unit = dialect?.units.find((u) => u.unit === unitKey) ?? dialect?.units[0]

  return (
    <div className="space-y-6">
      <SectionHeader title="Colloquial" arabic="عامية" subtitle={dialect?.where ?? 'Spoken, everyday Arabic.'} />
      {catalogue.isPending && <AnalyzerSkeleton />}
      {catalogue.isError && <Failed error={catalogue.error} onRetry={catalogue.refetch} />}
      {dialects.length > 1 && (
        <Segmented label="Dialect" options={asOptions(dialects, 'key', 'label')} value={dialect.key} onChange={(key) => { setDialectKey(key); setUnitKey(null) }} />
      )}
      {dialect?.units.length > 1 && (
        <Segmented label="Unit" options={asOptions(dialect.units, 'unit', 'title')} value={unit.unit} onChange={setUnitKey} />
      )}
      {unit && <Unit key={`${dialect.key}/${unit.unit}`} dialect={dialect.key} unit={unit.unit} />}
    </div>
  )
}
