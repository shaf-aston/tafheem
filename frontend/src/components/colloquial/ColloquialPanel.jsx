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
import { Accent } from '../../lib/theme/accent'
import { nameOfPlace, parsePlace, placeOf, switchPlace, trailOf } from '../../lib/colloquial/place'
import { TABS } from '../../lib/nav/tabs'
import { useArrivalWhenReady } from '../../lib/nav/useArrival'
import { warm } from '../../lib/api/warm'
import { DialectList, TopicList, UnitList } from './course/Lists'
import { Breadcrumbs, DialectSwitch } from './course/Breadcrumbs'
import TopicView from './topic/TopicView'
import WordsView from './words/WordsView'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import Screen from '../ui/display/Screen'
import SectionHeader from '../ui/display/SectionHeader'
import { AnalyzerSkeleton } from '../ui/feedback/Skeleton'
import StatusNote from '../ui/feedback/StatusNote'
import { markSeen } from '../../lib/colloquial/seen'

const BLURB = TABS.find((t) => t.id === 'colloq')?.blurb

function Topic({ dialect, unit, at, words }) {
  const { data, isPending, isError, error, refetch } = useQuery(colloquialUnitQuery(dialect, unit))
  if (isPending) return <AnalyzerSkeleton />
  if (isError) return <ErrorAlert title="Could not load the lessons" fallback="The Colloquial lessons could not be reached." error={error} onRetry={refetch} />
  return words || !data.lessons[at].phrases.length ? <WordsView unit={data} at={at} /> : <TopicView unit={data} at={at} />
}

// The next topic the dialect has written, so a learner flows on instead of climbing back out.
function NextTopic({ unit, at, onGo }) {
  const next = unit.lessons.findIndex((l, i) => i > at && l.written)
  if (next < 0) return null
  return (
    <button type="button" onClick={() => onGo(next)}
      className="press mt-12 w-full py-4 rounded-[var(--radius-md)] border border-[var(--border)] type-ui font-semibold text-[var(--text)] hover:border-[var(--border-hi)] focus-visible:outline-2 focus-visible:outline-[var(--primary)]">
      Next topic: {unit.lessons[next].title} →
    </button>
  )
}

export default function ColloquialPanel({ incoming, arrival, onVisit }) {
  const catalogue = useQuery(colloquialQuery)
  const dialects = catalogue.data?.dialects ?? []
  const [place, setPlace] = useState(null)
  // A link that named a unit or topic the dialect has not written opens the top; this says so, until the next step.
  const [lost, setLost] = useState(false)
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
    setLost(false)
    setPlace(there)
    const where = placeOf(there, dialects)
    if (typeof there?.at === 'number') markSeen(where)
    onVisit?.(where)
  }
  // An arrival names a place; followed during render so a reload paints on it, not the top first.
  if (useArrivalWhenReady(arrival, Boolean(catalogue.data))) {
    const found = parsePlace(incoming, dialects)
    setPlace(found)
    setLost(Boolean(incoming) && !found)
    if (typeof found?.at === 'number') markSeen(placeOf(found, dialects))
  }

  const steps = trailOf(place, dialects).map((step) => ({ label: step.label, go: () => go(step.place) }))

  // Every speaker icon below says its line in this dialect's own voice (lib/theme/accent.js).
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
          <Breadcrumbs steps={steps} />
          {dialects.length > 1 && <DialectSwitch dialects={dialects} current={dialect.key} onPick={(key) => go(switchPlace(place, key, dialects))} />}
        </div>
      )}

      {lost && <StatusNote>That link did not match a lesson here, so this is the start.</StatusNote>}

      {/* Each step down is a screen: it opens at its top, and back up lands where it was left. */}
      {catalogue.data && (
        <Screen id={placeOf(place, dialects) ?? 'top'} depth={!dialect ? 0 : !unit ? 1 : lessonAt === null ? 2 : 3}>
          {!dialect && <DialectList dialects={dialects} go={go} />}
          {dialect && !unit && <UnitList dialect={dialect} go={go} />}
          {unit && lessonAt === null && <TopicList dialect={dialect} unit={unit} go={go} />}
          {unit && lessonAt !== null && (
            <>
              <Topic dialect={dialect.key} unit={unit.unit} at={lessonAt} words={words} />
              <NextTopic unit={unit} at={lessonAt} onGo={(next) => go({ dialect: dialect.key, unit: unit.unit, at: next, words: false })} />
            </>
          )}
        </Screen>
      )}
    </div>
    </Accent.Provider>
  )
}
