/**
 * The path walked on this tab, with a way back to any of it.
 *
 * The Recent row answers "what have I looked up lately"; this answers "how did I
 * get here", which is the question a reader has after following a synonym three
 * words deep. It is drawn from lib/journey.js, the same list the browser's back
 * arrow moves through, so the two can never point at different places.
 *
 * Three weights, one line: where you are, what is behind, and what is ahead
 * after a step back. Ahead is faded rather than removed, because it is one
 * click away and removing it looked like it had been thrown out. Everything is
 * quiet by design, this is a way back, not a thing to read.
 *
 * The tab comes from the journey, not from a prop: it sits inside SectionHeader,
 * which is drawn by every panel and knows nothing about tabs.
 */
import { goBack, jumpTo, nearest, tabNow, trailFor, useJourney } from '../../lib/journey'
import { isArabic } from '../../lib/arabicText'
import { TRAIL_STEPS } from '../../lib/session'

import ArabicText from './ArabicText'

// Quiet, quieter, quietest. The one you are on is the only one at full strength.
const WEIGHT = {
  here: 'text-[var(--text-dim)]',
  past: 'text-[var(--text-faint)] underline decoration-dotted underline-offset-4',
  ahead: 'text-[var(--text-faint)] opacity-50 underline decoration-dotted underline-offset-4',
}

// A whole sentence is a step too (Nahw), and it cannot be allowed to run along
// the title. The full text stays on the hover title.
const ROOM_PER_STEP = 22
const brief = (text) =>
  (text.length > ROOM_PER_STEP ? `${text.slice(0, ROOM_PER_STEP).trim()}…` : text)

const Step = ({ text }) =>
  (isArabic(text) ? <ArabicText size="sm">{brief(text)}</ArabicText> : brief(text))

export default function Trail() {
  const { steps, at } = useJourney()
  const walked = trailFor(steps, tabNow(steps, at), at)
  const { shown, sliced } = nearest(walked, at, TRAIL_STEPS)

  // Nowhere to go: an arrow that does nothing is worse than no arrow. One word
  // still counts, the arrow leaves it for whatever the tab showed before.
  if (walked.length === 0 || (at < 1 && !walked.some((step) => step.index > at))) return null

  return (
    <nav
      aria-label="Where you have been"
      className="flex items-center gap-1.5 flex-wrap type-small
        text-[var(--text-faint)] min-w-0"
    >
      {at > 0 && (
        <button
          type="button"
          onClick={goBack}
          aria-label="Back"
          title="Back"
          className="shrink-0 opacity-60 hover:opacity-100 hover:text-[var(--c)]
            transition-opacity"
        >
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
            <path d="M19 12H5" />
            <path d="m12 19-7-7 7-7" />
          </svg>
        </button>
      )}

      {sliced && <span aria-hidden="true" className="opacity-40" title="Earlier steps">…</span>}

      {shown.map((step, n) => {
        const where = step.index === at ? 'here' : step.index < at ? 'past' : 'ahead'
        return (
          <span key={`${step.index}-${step.value}`} className="flex items-center gap-1.5">
            {(n > 0 || sliced) && <span aria-hidden="true" className="opacity-40">›</span>}
            {where === 'here' ? (
              // A link back to where we already are would move the browser's
              // index without moving the page, which is how a back press stops
              // working after one click.
              <span data-step="here" aria-current="page" title={step.value} className={WEIGHT.here}>
                <Step text={step.value} />
              </span>
            ) : (
              <button
                type="button"
                data-step={where}
                title={step.value}
                onClick={() => jumpTo(step.index)}
                className={`${WEIGHT[where]} hover:text-[var(--c)] hover:opacity-100
                  transition-colors`}
              >
                <Step text={step.value} />
              </button>
            )}
          </span>
        )
      })}
    </nav>
  )
}
