/**
 * Timelines: five stretches of time, from Adam to the final home.
 *
 * The tab fetches the library once (about fifty events, fixed for the life of
 * the backend) and owns two things only: which section is open (none: the board
 * of sections) and which event is read. Where each of those goes on the screen is lib/timelineLayout's job,
 * and what they say is the backend's.
 *
 * The place in the tab is written as "section/event", so ?tab=timelines&q=
 * seerah/hijrah opens that event, and the back arrow steps through the events
 * read rather than leaving the app.
 */
import { useState } from 'react'
import { useArrivalWhenReady } from '../lib/useArrival'
import { useQuery } from '@tanstack/react-query'

import { timelinesQuery } from '../api'
import { nameOfPlace, parsePlace, placeOf } from '../lib/timelineLayout'

import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import ErrorAlert from './ui/ErrorAlert'
import EmptyState from './ui/EmptyState'
import { AnalyzerSkeleton } from './ui/Skeleton'
import StatusNote from './ui/StatusNote'
import TimelineBoard from './TimelineBoard'
import TimelineSection from './TimelineSection'

const ALL = 'all'

export default function TimelinesPanel({ accent, incoming, arrival, onGo, onVisit }) {
  const { data, isPending, isError, error, refetch } = useQuery(timelinesQuery)
  const [science, setScience] = useState(ALL)
  const [place, setPlace] = useState(null)   // { section, event, report }

  // An arrival is a deep link, a link from another tab, or the back arrow
  // landing here. All three name a place in the same words the journey was
  // written in, so all three are read the same way: once per arrival, and once
  // on the first render that has the sections to check the name against.
  // See lib/useArrival for why this is adjusted during render, not in an effect.
  // A link naming an event that does not exist opens the tab plainly, and says so.
  const [missed, setMissed] = useState(false)
  if (useArrivalWhenReady(arrival, Boolean(data))) {
    const asked = parsePlace(incoming, data.sections)
    if (asked) setPlace(asked)
    setMissed(Boolean(incoming) && !asked)
  }

  // The header keeps its place while the library loads; the science filter has
  // nothing to list yet, so it waits with only "All".
  if (isPending) {
    return (
      <div className="panel">
        <SectionHeader
          title="Timelines"
          arabic="التاريخ"
          aside={<div inert><Segmented label="Science" options={[{ id: ALL, label: 'All' }]} value={ALL} onChange={() => {}} accent={accent} wrap /></div>}
        />
        <AnalyzerSkeleton />
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorAlert title="Could not load the timelines" error={error} fallback="The timelines could not be reached." onRetry={refetch} />
    )
  }

  const go = (next) => {
    setMissed(false)
    setPlace(next)
    if (next) onVisit?.(placeOf(next.section, next.event, next.report))
  }
  const pick = (sectionId) => (eventId) => go({ section: sectionId, event: eventId || null })
  const report = (sectionId, eventId) => (ref) => go({ section: sectionId, event: eventId, report: ref })

  const shown = data.sections.filter((s) => science === ALL || s.science === science)
  // A science filter that hides the open section sends the tab back to the board.
  const section = shown.find((s) => s.id === place?.section)
  const filter = [
    { id: ALL, label: 'All' },
    ...data.sciences.map((s) => ({ id: s.key, label: s.name })),
  ]

  return (
    <div className="panel">
      <SectionHeader
        title="Timelines"
        arabic="التاريخ"
        nameOf={(q) => nameOfPlace(q, data.sections)}
        aside={<Segmented label="Science" options={filter} value={science} onChange={setScience} accent={accent} wrap />}
      />

      {missed && (
        <StatusNote>That link names a timeline event that does not exist, so the sections are shown.</StatusNote>
      )}

      {shown.length === 0
        ? <EmptyState>No section is filed under that science.</EmptyState>
        : (
          <>
            <TimelineBoard sections={shown} current={section?.id ?? null} onPick={(id) => go(id && { section: id, event: null })} />
            {section && (
              <TimelineSection
                key={section.id}
                section={section}
                library={data}
                chosen={section.events.find((e) => e.id === place.event) ?? null}
                report={place.report ?? null}
                onPick={pick(section.id)}
                onReport={report(section.id, place.event)}
                onGo={onGo}
              />
            )}
          </>
        )}
    </div>
  )
}
