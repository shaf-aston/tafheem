/**
 * Timelines: five stretches of time, from Adam to the final home.
 *
 * The tab fetches the library once (about fifty events, fixed for the life of
 * the backend) and owns two things only: which section is open and which event
 * is read. Where each of those goes on the screen is lib/timelineLayout's job,
 * and what they say is the backend's.
 *
 * The place in the tab is written as "section/event", so ?tab=timelines&q=
 * seerah/hijrah opens that event, and the back arrow steps through the events
 * read rather than leaving the app.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getTimelines } from '../api'
import { smartError } from '../lib/apiError'
import { parsePlace, placeOf } from '../lib/timelineLayout'

import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import EmptyState from './ui/EmptyState'
import { AnalyzerSkeleton } from './ui/Skeleton'
import TimelineSection from './TimelineSection'

const ALL = 'all'

export default function TimelinesPanel({ accent, incoming, arrival, onGo, onVisit }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['timelines'],
    queryFn: getTimelines,
    staleTime: Infinity,
  })
  const [science, setScience] = useState(ALL)
  const [place, setPlace] = useState(null)   // { section, event, report }

  // An arrival is a deep link, a link from another tab, or the back arrow
  // landing here. All three name a place in the same words the journey was
  // written in, so all three are read the same way: once per arrival, and once
  // on the first render that has the sections to check the name against.
  //
  // Adjusted during render rather than in an effect, the pattern React blesses
  // for following a prop (see lib/useArrival): the corrected render is the
  // first one painted, so a deep link never shows the shut tab for a frame.
  const [seenLink, setSeenLink] = useState(null)
  // A link naming an event that does not exist opens the tab plainly, and says so.
  const [missed, setMissed] = useState(false)
  const link = `${arrival}:${incoming}`
  if (data && link !== seenLink) {
    setSeenLink(link)
    const asked = parsePlace(incoming, data.sections)
    if (asked) setPlace(asked)
    setMissed(Boolean(incoming) && !asked)
  }

  if (isPending) return <AnalyzerSkeleton />

  if (isError) {
    return (
      <ErrorAlert title="Could not load the timelines">
        {smartError(error, 'The timelines could not be reached.')}
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }

  const go = (next) => {
    setMissed(false)
    setPlace(next)
    if (next) onVisit?.(placeOf(next.section, next.event, next.report))
  }
  // A section shutting is only news when it is the open one: opening another
  // shuts this one through its own prop, and that close must not clear the
  // section just opened (a controlled <details> reports both).
  const open = (id, isOpen) => {
    if (isOpen) go({ section: id, event: place?.section === id ? place.event : null })
    else if (place?.section === id) go(null)
  }
  const pick = (sectionId) => (eventId) => go(eventId ? { section: sectionId, event: eventId } : { section: sectionId, event: null })
  const report = (sectionId, eventId) => (ref) => go({ section: sectionId, event: eventId, report: ref })

  const shown = data.sections.filter((s) => science === ALL || s.science === science)
  const filter = [
    { id: ALL, label: 'All' },
    ...data.sciences.map((s) => ({ id: s.key, label: s.name })),
  ]

  return (
    <div className="space-y-3">
      <SectionHeader
        title="Timelines"
        arabic="التاريخ"
        aside={<Segmented label="Science" options={filter} value={science} onChange={setScience} accent={accent} wrap />}
      />

      {missed && (
        <p role="status" className="type-small text-[var(--text-dim)]">
          That link names a timeline event that does not exist, so every section is shown.
        </p>
      )}

      {shown.length === 0
        ? <EmptyState>No section is filed under that science.</EmptyState>
        : shown.map((section) => {
          const isOpen = place?.section === section.id
          return (
            <TimelineSection
              key={section.id}
              section={section}
              library={data}
              open={isOpen}
              alone={shown.length === 1}
              chosen={isOpen ? section.events.find((e) => e.id === place.event) ?? null : null}
              report={isOpen ? place.report ?? null : null}
              onOpen={open}
              onPick={pick(section.id)}
              onReport={report(section.id, place?.event)}
              onGo={onGo}
            />
          )
        })}
    </div>
  )
}
