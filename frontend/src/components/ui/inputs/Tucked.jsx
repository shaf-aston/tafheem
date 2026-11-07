/**
 * A question form that tucks itself away once its answer is on screen.
 *
 * Over an answer the box, its chips and its filters were a screen of controls
 * the reader had already used, and on a phone the answer started below the
 * fold. So once `answer` arrives the form folds into one slim pill holding the
 * question, and the answer is the next thing down. Tapping the pill opens the
 * form again with the cursor in the box; the next answer tucks it again.
 *
 * Keyed on the answer itself rather than a flag: a reopened form stays open
 * while it is used, and a new answer (a different object) folds it back
 * without any effect having to notice.
 *
 * The folded form stays in the page, inert, so what was typed in it survives
 * and the fold can be animated (styles/components.css, Tucked).
 */
import { useId, useRef, useState } from 'react'
import { flushSync } from 'react-dom'

import ArabicText from '../text/ArabicText'
import { isArabic } from '../../../lib/text/arabicText'

export default function Tucked({ answer, query = '', accent, children }) {
  const [reopenedOver, setReopenedOver] = useState(null)
  const tucked = Boolean(answer) && Boolean(query.trim()) && reopenedOver !== answer
  const form = useRef(null)
  const id = useId()

  // Opened in one go so the box is no longer inert when it is focused.
  const reopen = () => {
    flushSync(() => setReopenedOver(answer))
    form.current.querySelector('input, textarea')?.focus()
  }

  return (
    <div className="tucked" style={{ '--c': accent }}>
      {tucked && (
        <button
          type="button"
          onClick={reopen}
          aria-expanded="false"
          aria-controls={id}
          aria-label={`Edit the question: ${query}`}
          className="tucked-pill press tap fade-in"
        >
          {isArabic(query)
            ? <ArabicText size="sm" className="tucked-query">{query}</ArabicText>
            : <span className="tucked-query type-ui">{query}</span>}
          <svg viewBox="0 0 16 16" className="w-4 h-4 shrink-0" fill="none" stroke="currentColor"
            strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M11 2.5 13.5 5 6 12.5 3 13l.5-3z" />
            <path d="m9.5 4 2.5 2.5" />
          </svg>
        </button>
      )}
      <div id={id} className="tucked-form" data-tucked={tucked || undefined} inert={tucked}>
        <div ref={form} className="tucked-inner space-y-3">{children}</div>
      </div>
    </div>
  )
}
