/**
 * One chosen stretch of time: its heading, a rail of its events, and the opened
 * event read underneath. The map is a small toggle by the heading, off unless
 * the reader turned it on last time, so the first screen is the story.
 *
 * Every section wears its own hue (timelines.json), set once here and read by
 * everything inside as --tl-acc.
 */
import { useEffect, useRef, useState } from 'react'

import Chip from './ui/Chip'
import TimelineRail from './TimelineRail'
import TimelineEvent from './TimelineEvent'
import TimelineMap from './TimelineMap'
import AsbabPanel from './AsbabPanel'
import { pinsOf, placeOfStep, sectionLook } from '../lib/timelineLayout'
import { scrollToEl } from '../lib/scrollToEl'
import { useRememberedFlag } from '../lib/useRemembered'

const ACCENT = 'var(--tl-acc)'

export default function TimelineSection({ section, library, chosen, report, onPick, onReport, onGo }) {
  const [showMap, setShowMap] = useRememberedFlag('timeline-map-open', false)
  const { hue } = sectionLook(section.id)
  // The step being read, shared by the steps, the map and the where-am-I line.
  // Held with its event, so opening another event starts with none.
  const [focus, setFocus] = useState(null)
  const here = chosen && focus?.event === chosen.id ? focus.step : null
  const onHere = (step) => setFocus(step ? { event: chosen.id, step } : null)
  const at = chosen ? (here ? placeOfStep(chosen, here) : chosen.place ?? null) : null

  // Opening an event brings its reader to the top of the screen.
  const reader = useRef(null)
  const chosenId = chosen?.id
  useEffect(() => {
    if (chosenId) scrollToEl(reader.current, 'top')
  }, [chosenId])

  return (
    <section className="tl-hue space-y-3" style={{ '--h': hue }}>
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          {/* The chosen tile above already names it, English and Arabic. On a
              phone the tiles keep only the Arabic, so the name is shown here
              there alone; wider, it stays for screen readers. */}
          <h3 className="text-lg font-semibold text-[var(--text)] min-[521px]:sr-only">{section.name}</h3>
          <p className="type-small text-[var(--text-dim)]">{section.sub}</p>
        </div>
        {section.map && (
          <Chip selected={showMap} accent={ACCENT} onClick={() => setShowMap(!showMap)}>
            Map · {pinsOf(section, library.places).length} places
          </Chip>
        )}
      </div>

      {section.map && showMap && (
        <TimelineMap section={section} library={library} accent={ACCENT} chosen={chosen} at={at} onPick={onPick} />
      )}

      <TimelineRail section={section} library={library} chosenId={chosen?.id ?? null} onPick={onPick} />

      {chosen && (
        <div ref={reader} className="space-y-4 scroll-mt-[calc(var(--app-header-h,0px)+1rem)]">
          <TimelineEvent
            section={section}
            event={chosen}
            library={library}
            accent={ACCENT}
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
              accent={ACCENT}
              chosen={report}
              onChoose={onReport}
              onGo={onGo}
            />
          )}
        </div>
      )}
    </section>
  )
}
