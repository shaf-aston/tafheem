/**
 * Colloquial: spoken Arabic, one step down at a time.
 *
 * Dialect, then unit, then topic, then the words. Only the current step is on
 * screen, with a trail above it to climb back up, so a learner is never shown
 * sixteen units and sixty topics at once. The catalogue (titles only) draws the
 * first three steps; the unit itself is fetched only once a topic is opened.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { colloquialQuery, colloquialUnitQuery } from '../../api'
import { Accent } from '../../lib/accent'
import { nameOfPlace, parsePlace, placeOf, switchPlace, trailOf } from '../../lib/colloquial/place'
import { TABS } from '../../lib/tabs'
import { useArrivalWhenReady } from '../../lib/useArrival'
import { warm } from '../../lib/warm'
import { DialectList, TopicList, UnitList } from './course/Lists'
import { Switch, Trail } from './course/Trail'
import TopicView from './topic/TopicView'
import WordsView from './words/WordsView'
import ErrorAlert from '../ui/ErrorAlert'
import SectionHeader from '../ui/SectionHeader'
import { AnalyzerSkeleton } from '../ui/Skeleton'

const BLURB = TABS.find((t) => t.id === 'colloq')?.blurb

function Topic({ dialect, unit, at, words }) {
  const { data, isPending, isError, error, refetch } = useQuery(colloquialUnitQuery(dialect, unit))
  if (isPending) return <AnalyzerSkeleton />
  if (isError) return <ErrorAlert title="Could not load the lessons" fallback="The Colloquial lessons could not be reached." error={error} onRetry={refetch} />
  return words || !data.lessons[at].phrases.length ? <WordsView unit={data} at={at} /> : <TopicView unit={data} at={at} />
}

export default function ColloquialPanel({ incoming, arrival, onVisit }) {
  const catalogue = useQuery(colloquialQuery)
  const dialects = catalogue.data?.dialects ?? []
  const [place, setPlace] = useState(null)
  const client = useQueryClient()

  const dialect = place && dialects.find((d) => d.key === place.dialect)
  const unit = dialect?.units.find((u) => u.written && u.unit === place.unit)
  const lessonAt = place?.at ?? null
  const words = place?.words ?? false
  // A dialect, unit or word list arrives finished; a lesson's next step still moves.
  // Opening a unit shows its topics; the unit's words are what a topic click needs.
  useEffect(() => {
    if (dialect && unit) warm(client, colloquialUnitQuery(dialect.key, unit.unit))
  }, [client, dialect, unit])

  // One way to move: every step down or up the tree is a place on the journey,
  // so a reload, a pasted link and the back arrow all land where the reader was.
  const go = (there) => {
    setPlace(there)
    onVisit?.(placeOf(there, dialects))
  }
  // An arrival names a place; followed during render so a reload paints on it, not the top first.
  if (useArrivalWhenReady(arrival, Boolean(catalogue.data))) setPlace(parsePlace(incoming, dialects))

  const steps = trailOf(place, dialects).map((step) => ({ label: step.label, go: () => go(step.place) }))

  // Every speaker icon below says its line in this dialect's own voice (lib/accent.js).
  return (
    <Accent.Provider value={dialect?.key ?? null}>
    <div className="panel">
      <SectionHeader tab="colloq" subtitle={dialect ? [dialect.gloss, dialect.where].filter(Boolean).join(' · ') : BLURB}
        nameOf={(q) => nameOfPlace(q, dialects)} history={false} />
      {catalogue.isPending && <AnalyzerSkeleton />}
      {catalogue.isError && <ErrorAlert title="Could not load the lessons" fallback="The Colloquial lessons could not be reached." error={catalogue.error} onRetry={catalogue.refetch} />}
      {/* At the top the subtitle already says these are the dialects: the trail starts one step down. */}
      {catalogue.data && dialect && (
        <div className="flex flex-wrap items-center gap-3 pb-5 border-b border-[var(--border)]">
          <Trail steps={steps} />
          {dialects.length > 1 && <Switch dialects={dialects} current={dialect.key} onPick={(key) => go(switchPlace(place, key, dialects))} />}
        </div>
      )}

      {catalogue.data && !dialect && <DialectList dialects={dialects} go={go} />}
      {dialect && !unit && <UnitList dialect={dialect} go={go} />}
      {unit && lessonAt === null && <TopicList dialect={dialect} unit={unit} go={go} />}

      {unit && lessonAt !== null && (
        <div key={`${unit.unit}/${lessonAt}/${words}`} className="rise-in">
          <Topic dialect={dialect.key} unit={unit.unit} at={lessonAt} words={words} />
        </div>
      )}
    </div>
    </Accent.Provider>
  )
}
