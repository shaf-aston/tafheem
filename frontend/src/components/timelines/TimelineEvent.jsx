/**
 * One event, opened: a tinted header (section, title, when and where), then
 * the summary, the hadith words, and the steps as a numbered run below it.
 * Steps are open on arrival (TimelineSteps); an event nobody has broken down
 * yet simply has none. Cautions about the event stay in view, and the places
 * it is told sit behind one "Sources" pill.
 *
 * Where a reference opens is TimelineRefs, shared with those steps.
 *
 * The pinned year: once the header has scrolled up out of sight, the event's
 * year and title stay pinned at the top of the screen (.tl-year-pin), so a reader
 * deep in the steps still knows when they are.
 */
import { useMemo, useState } from 'react'

import ArabicText from '../ui/text/ArabicText'
import { useInView } from '../../lib/motion/useInView'
import Chip from '../ui/inputs/Chip'
import TopicIcon from '../ui/display/TopicIcon'
import TimelineHadith from './TimelineHadith'
import TimelineRefs from '../ui/text/TimelineRefs'
import TimelineSteps from './TimelineSteps'
import TimelineWhere from './TimelineWhere'
import { printedBy } from '../../lib/hadith/hadithWords'
import { NO_DATE, TRAD, isDated, sectionLook } from '../../lib/timelines/look'

export default function TimelineEvent({ section, event, library, accent, onGo, here, onHere, onPick, at }) {
  const place = event.place ? library.places[event.place] : null
  const steps = event.steps ?? []
  const [showSources, setShowSources] = useState(false)
  // Said beside the place it qualifies; as a pill on its own it read as a
  // strange heading with nothing after it.
  const traditional = event.flags?.includes(TRAD)
  const cautions = event.flags?.filter((f) => f !== TRAD)
  const facts = [
    event.when,
    // "624 CE, 2 AH" already says 2 AH; a second chip saying it again said nothing.
    event.hijri && !event.when?.includes(event.hijri) ? event.hijri : null,
    place ? `${place.name}${traditional ? `, ${library.flags[TRAD]}` : ''}` : null,
  ].filter(Boolean)
  // One hadith often tells the event and its steps alike; whoever cites it
  // first prints its words and the rest keep their number alone.
  const prints = useMemo(() => printedBy(event), [event])
  const refs = event.refs ?? []
  // The header counts as gone once it is under the app's own pinned header.
  const [margin] = useState(() => `-${parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--app-header-h')) || 0}px 0px 0px 0px`)
  const [head, headInView] = useInView({ once: false, margin })
  const year = event.when ?? event.hijri

  return (
    <article className="tl-reader">
      {year && (
        <div className="tl-year-pin" data-on={!headInView} aria-hidden="true">
          <div><span className="tl-year-pin-year">{year}</span><span className="tl-year-pin-title">{event.title}</span></div>
        </div>
      )}
      <header ref={head} className="tl-head">
        <span className="tl-clip"><TopicIcon topic={sectionLook(section.id).icon} className="tl-ico" /></span>
        <TimelineWhere section={section} event={event} here={here} onHere={onHere} onPick={onPick} />
        <h3>{event.title}</h3>
        <ArabicText className="tl-ar arabic-inline block">{event.arabic}</ArabicText>
        <div className="tl-facts">
          {facts.map((fact) => <span key={fact} className="tl-chip">{fact}</span>)}
        </div>
      </header>

      <div className="p-4 space-y-3">
        <div>
          <p className="tl-layer">Summary</p>
          <p className="text-[var(--text)] leading-relaxed max-w-prose">{event.summary}</p>
        </div>

        {/* Each estimate beside the one source that states it; none is ours. */}
        {isDated(section) && (
          <div>
            <p className="tl-layer">When, estimated</p>
            {event.dates.length === 0 && <p className="text-[var(--text-dim)]">{NO_DATE}</p>}
            <ul className="space-y-1.5">
              {event.dates.map((date) => (
                <li key={date.says} className="flex flex-wrap items-center gap-2 text-[var(--text)]">
                  <span>{date.says}</span>
                  <TimelineRefs refs={[date.ref]} library={library} accent={accent} onGo={onGo} />
                </li>
              ))}
            </ul>
          </div>
        )}

        <TimelineRefs flags={cautions} library={library} accent={accent} onGo={onGo} />

        <TimelineHadith refs={event.refs} only={prints.get('')} library={library} accent={accent} />

        {steps.length > 0 && (
          // Keyed by event, so each one opens with its own side details folded.
          <TimelineSteps
            key={event.id}
            steps={steps}
            prints={prints}
            library={library}
            accent={accent}
            onGo={onGo}
            here={here}
            onHere={onHere}
            at={at}
          />
        )}

        {refs.length > 0 && (
          <div className="pt-3 border-t border-[var(--border)] space-y-2">
            <Chip selected={showSources} accent={accent} onClick={() => setShowSources(!showSources)}>
              Sources {refs.length}
            </Chip>
            {showSources && <TimelineRefs refs={refs} library={library} accent={accent} onGo={onGo} />}
          </div>
        )}
      </div>
    </article>
  )
}
