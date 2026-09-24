/**
 * The line down a section, as in the chosen prototype: one thin rule, one row
 * per event with its year (or stage) and how many steps it holds. No dots and no gap
 * labels; the years already say how far apart things are.
 *
 * A row resting on a weak narration is drawn fainter, still there and still
 * readable, so the reader sees it is on softer ground before opening it.
 */
import { countSteps } from '../lib/timelineLayout'

const WEAK = 'weakchain'

export default function TimelineAxis({ section, library, accent, chosenId, onPick, className = '' }) {
  return (
    <ol
      // Pinned beside a long story, and scrolling on its own if it is the taller.
      className={`${className} list-none m-0 p-0 border-s-2 md:sticky md:top-[calc(var(--app-header-h,0px)+1rem)] md:max-h-[calc(100vh-var(--app-header-h,0px)-2rem)] md:overflow-y-auto [scrollbar-width:thin] [scrollbar-color:var(--border)_transparent]`}
      style={{ borderColor: `color-mix(in srgb, ${accent} 25%, transparent)` }}
    >
      {section.events.map((event) => {
        const on = event.id === chosenId
        const inside = countSteps(event.steps)
        const weak = event.flags?.includes(WEAK)
        return (
          <li key={event.id}>
            <button
              type="button"
              onClick={() => onPick(on ? null : event.id)}
              aria-current={on}
              title={[event.when, event.place && library.places[event.place]?.name, weak && library.flags[WEAK]].filter(Boolean).join(' · ')}
              style={on ? { boxShadow: `inset 2px 0 0 ${accent}` } : undefined}
              className={`w-full flex items-baseline text-start text-sm leading-snug px-2.5 py-1.5
                rounded-e-[var(--radius-sm)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]
                ${on ? 'bg-[var(--surface-hi)] font-semibold text-[var(--text)]'
                  // Faint rather than dimmed further by opacity, which fell under readable contrast.
                  : weak ? 'text-[var(--text-faint)] italic' : 'text-[var(--text-dim)]'}`}
            >
              {/* Every section has the same column, so they all read as one line.
                  Dated: the year. Otherwise: the stage, whole numbers only, so
                  events sharing a number (the minor signs) have no set order.
                  Fixed widths so the titles line up. */}
              <span className="shrink-0 flex gap-1.5 me-2 type-tiny font-normal tabular-nums text-[var(--text-faint)]">
                <span className="w-7">{Math.trunc(event.at)}</span>
                {section.kind === 'dated' && <span className="w-9">{event.hijri}</span>}
              </span>
              <span className="min-w-0">
                {event.title}
                {inside > 0 && (
                  <span
                    className="ms-1.5 type-tiny font-normal tabular-nums"
                    style={{ color: accent }}
                    title={`${inside} steps inside`}
                  >
                    +{inside}<span className="sr-only"> steps inside</span>
                  </span>
                )}
                {weak && <span className="sr-only"> ({library.flags[WEAK]})</span>}
              </span>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
