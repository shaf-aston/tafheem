/**
 * One event, opened: what happened, where, where it is told, and what happened
 * inside it.
 *
 * The reader half of the tab. The line of events stays on the left and this
 * fills the right as the chapter for the one that is open, with its steps as a
 * numbered run below the summary (TimelineSteps), open on arrival. An event
 * nobody has broken down yet simply has no run, and says so.
 *
 * Where it is told is TimelineRefs, shared with those steps.
 */
import { useMemo } from 'react'

import ArabicText from './ui/ArabicText'
import TimelineHadith from './TimelineHadith'
import TimelineRefs from './TimelineRefs'
import TimelineSteps from './TimelineSteps'
import TimelineWhere from './TimelineWhere'
import { printedBy } from '../lib/hadithWords'
import { TRAD } from '../lib/timelineLayout'

export default function TimelineEvent({ section, event, library, accent, onGo, here, onHere, onPick, at }) {
  const place = event.place ? library.places[event.place] : null
  const steps = event.steps ?? []
  // Said beside the place it qualifies; as a pill on its own it read as a
  // strange heading with nothing after it.
  const traditional = event.flags?.includes(TRAD)
  // One hadith often tells the event and its steps alike; whoever cites it
  // first prints its words and the rest keep their number alone.
  const prints = useMemo(() => printedBy(event), [event])

  return (
    <article className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-3">
      <TimelineWhere section={section} event={event} here={here} onHere={onHere} onPick={onPick} />
      <div className="flex items-baseline gap-2 flex-wrap">
        <h3 className="text-lg font-semibold text-[var(--text)]">{event.title}</h3>
        <ArabicText className="arabic-inline text-[var(--text-faint)]">{event.arabic}</ArabicText>
      </div>
      <p className="type-small text-[var(--text-faint)]">
        {event.when}{place ? ` · ${place.name}` : ''}
        {place && traditional && `, ${library.flags[TRAD]}`}
      </p>
      <p className="text-[var(--text-dim)] leading-relaxed max-w-prose">{event.summary}</p>

      <TimelineRefs
        flags={event.flags?.filter((f) => f !== TRAD)}
        refs={event.refs}
        library={library}
        accent={accent}
        onGo={onGo}
        className="pt-1"
      />

      <TimelineHadith refs={event.refs} only={prints.get('')} library={library} accent={accent} className="pt-1" />

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
    </article>
  )
}
