/**
 * One stretch of time: shut it is a line saying how many events are in it, open
 * it is a thin line of events on the left and the opened event filling the
 * rest. The map waits folded above the story: shut unless the reader opened it
 * last time, so the first screen is the story, as in the chosen prototype.
 *
 * Opening is the app's own Disclosure, controlled from the panel so that opening
 * one shuts the rest: five sections open at once is a page nobody reads down.
 * Every section wears the same colour and shape: the Seerah was the one people
 * liked, and a striped, lilac unseen section read as a different design.
 */
import { useState } from 'react'

import ArabicText from './ui/ArabicText'
import Disclosure from './ui/Disclosure'
import TimelineAxis from './TimelineAxis'
import TimelineEvent from './TimelineEvent'
import TimelineMap from './TimelineMap'
import AsbabPanel from './AsbabPanel'
import { lineWidth, pinsOf, placeOfStep } from '../lib/timelineLayout'
import { useRememberedFlag } from '../lib/useRemembered'

export default function TimelineSection({ section, library, open, alone, chosen, report, onOpen, onPick, onReport, onGo }) {
  const [showMap, setShowMap] = useRememberedFlag('timeline-map-open', false)
  const accent = 'var(--tab-timelines)'
  // The step being read, shared by the steps, the map and the where-am-I line.
  // Held with its event, so opening another event starts with none.
  const [focus, setFocus] = useState(null)
  const here = chosen && focus?.event === chosen.id ? focus.step : null
  const onHere = (step) => setFocus(step ? { event: chosen.id, step } : null)
  const at = chosen ? (here ? placeOfStep(chosen, here) : chosen.place ?? null) : null

  const label = (
    <span className="flex items-baseline gap-2 flex-wrap min-w-0">
      <span className="text-base font-semibold text-[var(--text)]">{section.name}</span>
      <ArabicText size="sm" className="arabic-inline text-[var(--text-faint)]">{section.arabic}</ArabicText>
      <span className="type-tiny text-[var(--text-faint)] truncate">{section.sub}</span>
      {section.kind === 'unseen' && (
        <span className="sr-only">Unseen: known by revelation, not by history.</span>
      )}
      {!alone && (
        <span className="type-tiny ms-auto shrink-0" style={{ color: accent }}>
          {open ? 'Close' : `${section.events.length} events`}
        </span>
      )}
    </span>
  )

  const body = (
      <div
        className="grid gap-x-8 gap-y-6 items-start md:grid-cols-[minmax(0,var(--timeline-line))_minmax(0,1fr)]"
        style={{ '--timeline-line': lineWidth }}
      >
        {/* The line is written first, so Tab reaches the events before the
            reader's pins and links, as the eye does on a wide screen. On a phone
            it is shown second: above the reader it would be scrolling past the
            whole Seerah to see the event just tapped. */}
        <TimelineAxis
          section={section}
          library={library}
          accent={accent}
          chosenId={chosen?.id ?? null}
          onPick={onPick}
          className="order-2 md:order-none"
        />
        <div className="min-w-0 space-y-4">
          {section.map && (
            // The map is for finding a place; once found it only pushes the
            // story down, so it is shut by default and the choice remembered.
            <Disclosure
              label={`Map · ${pinsOf(section, library.places).length} places`}
              defaultOpen={showMap}
              onToggle={setShowMap}
              bodyClassName="pt-2"
            >
              <TimelineMap section={section} library={library} accent={accent} chosen={chosen} at={at} onPick={onPick} />
            </Disclosure>
          )}
          {chosen
            ? (
              <>
                <TimelineEvent
                  section={section}
                  event={chosen}
                  library={library}
                  accent={accent}
                  onGo={onGo}
                  here={here}
                  onHere={onHere}
                  onPick={onPick}
                  at={at}
                />
                {/* Only where there is something in it: an event nobody wrote a
                    report about should not offer an empty panel. */}
                {chosen.asbab > 0 && (
                  <AsbabPanel
                    section={section}
                    event={chosen}
                    accent={accent}
                    chosen={report}
                    onChoose={onReport}
                    onGo={onGo}
                  />
                )}
              </>
            )
            : (
              <p className="text-sm text-[var(--text-dim)]">
                {section.map ? 'Tap an event, or a pin on the map.' : 'Tap an event to read it.'}
              </p>
            )}
        </div>
      </div>
  )

  // The only section on screen has nothing to fold away from, so it is simply open.
  if (alone) {
    return (
      <section className="rounded-[var(--radius-md)] border border-[var(--border)]">
        <header className="px-4 py-3">{label}</header>
        <div className="p-5 border-t border-[var(--border)]">{body}</div>
      </section>
    )
  }

  return (
    <Disclosure
      framed
      label={label}
      defaultOpen={open}
      onToggle={(isOpen) => onOpen(section.id, isOpen)}
      bodyClassName="p-5 border-t border-[var(--border)]"
    >
      {body}
    </Disclosure>
  )
}
