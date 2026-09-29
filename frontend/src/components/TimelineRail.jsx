/**
 * A section's events as one horizontal rail of cards, dots on a line above.
 *
 * No scrollbar: the edges fade and round arrows page it, hiding at the ends
 * (a phone just swipes). The opened event's card is brought into view on
 * arrival, so a deep link never lands on a rail scrolled past it.
 *
 * An event resting on a weak narration keeps its card, drawn with a dashed
 * edge and said in words for a screen reader, as the old line did.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import ArabicText from './ui/ArabicText'
import TileCard from './ui/TileCard'
import { eventIcon, sectionLook } from '../lib/timelineLayout'

const WEAK = 'weakchain'
const PAGE = 0.8   // share of the visible width one arrow press moves
const EDGE = 4     // px of slack before an end counts as reached

export default function TimelineRail({ section, library, chosenId, onPick }) {
  const strip = useRef(null)
  const [ends, setEnds] = useState({ start: true, end: false })
  const { hue } = sectionLook(section.id)

  const measure = useCallback(() => {
    const el = strip.current
    if (!el) return
    setEnds({ start: el.scrollLeft < EDGE, end: el.scrollLeft + el.clientWidth >= el.scrollWidth - EDGE })
  }, [])

  useEffect(() => {
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [measure, section.id])

  // Centre the opened card in the strip only: scrollIntoView would move the page too.
  useEffect(() => {
    const el = strip.current
    const card = el?.querySelector('[aria-current="true"]')
    if (!card) return
    el.scrollTo({ left: card.offsetLeft - (el.clientWidth - card.offsetWidth) / 2 })
  }, [chosenId, section.id])

  const page = (dir) => {
    const el = strip.current
    el.scrollBy({ left: dir * el.clientWidth * PAGE, behavior: 'smooth' })
  }

  return (
    <div className="tl-rail tl-hue" style={{ '--h': hue }}>
      <button type="button" className="tl-arrow tl-arrow-l" aria-label="Earlier" disabled={ends.start} onClick={() => page(-1)}>
        &#8249;
      </button>
      <div ref={strip} className="tl-strip" tabIndex={0} aria-label={`${section.name} timeline`} onScroll={measure}>
        <div className="tl-strip-in">
          {section.events.map((event, i) => {
            const on = event.id === chosenId
            const weak = event.flags?.includes(WEAK)
            const inside = event.steps?.length ?? 0
            return (
              <TileCard
                key={event.id}
                variant="event"
                className={`tl-rail-card${weak ? ' tl-weak' : ''}`}
                hue={hue}
                icon={eventIcon(i)}
                index={i}
                current={on}
                onClick={() => onPick(on ? null : event.id)}
              >
                {/* Dated sections show the year; the others the stage. */}
                <span className="tl-chip">{section.kind === 'dated' && event.hijri ? event.hijri : event.when}</span>
                <h4 className="tl-title">{event.title}</h4>
                <ArabicText size="sm" className="tl-ar arabic-inline">{event.arabic}</ArabicText>
                <p className="tl-sum">{event.summary}</p>
                <span className="tl-meta">
                  {inside ? `${inside} ${inside === 1 ? 'step' : 'steps'}` : 'Read'}
                  {weak && <span className="sr-only"> ({library.flags[WEAK]})</span>}
                </span>
              </TileCard>
            )
          })}
        </div>
      </div>
      <button type="button" className="tl-arrow tl-arrow-r" aria-label="Later" disabled={ends.end} onClick={() => page(1)}>
        &#8250;
      </button>
    </div>
  )
}
