/**
 * One event, opened: a tinted header (section, title, when and where), then
 * the summary, the hadith words, and the steps as a numbered run below it.
 * Steps are open on arrival (TimelineSteps); an event nobody has broken down
 * yet simply has none. Cautions about the event stay in view, and the places
 * it is told sit behind one "Sources" pill.
 *
 * Where a reference opens is TimelineRefs, shared with those steps.
 */
import { useMemo, useState } from 'react'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import TopicIcon from './ui/TopicIcon'
import TimelineHadith from './TimelineHadith'
import TimelineRefs from './TimelineRefs'
import TimelineSteps from './TimelineSteps'
import TimelineWhere from './TimelineWhere'
import { printedBy } from '../lib/hadithWords'
import { TRAD, sectionLook } from '../lib/timelineLayout'

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
    event.hijri && event.hijri !== event.when ? event.hijri : null,
    place ? `${place.name}${traditional ? `, ${library.flags[TRAD]}` : ''}` : null,
  ].filter(Boolean)
  // One hadith often tells the event and its steps alike; whoever cites it
  // first prints its words and the rest keep their number alone.
  const prints = useMemo(() => printedBy(event), [event])
  const refs = event.refs ?? []

  return (
    <article className="tl-reader">
      <header className="tl-head">
        <span className="tl-clip"><TopicIcon topic={sectionLook(section.id).icon} className="tl-ico" /></span>
        <TimelineWhere section={section} event={event} here={here} onHere={onHere} onPick={onPick} />
        <span className="tl-chip mt-2 inline-block">{section.name}</span>
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
