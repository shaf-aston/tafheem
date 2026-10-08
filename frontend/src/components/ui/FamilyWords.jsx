/**
 * The tellings of a number side by side in words: each telling's matn with the words only it has underlined and the
 * words that match another telling's only once the dots are gone dotted, the other telling's word beside them.
 * Neutral on purpose: a difference is shown, never called an addition or a mistake. Tapping the letter opens that hadith.
 */
import { markedRuns } from '../../lib/familyWords'

import ArabicText from './ArabicText'
import ShowRest from './ShowRest'

export default function FamilyWords({ parts, accent, onOpen }) {
  return (
    <div className="space-y-2">
      <p className="type-tiny m-0 text-[var(--text-faint)]">
        Underlined: only in this telling. Dotted: matches a word of another telling once the dots are taken off.
      </p>
      <ul className="list-none m-0 p-0">
        {parts.filter((p) => p.marks.length).map((p) => (
          <li key={p.part} className="py-2 border-t border-[var(--border)] first:border-t-0 flex items-start gap-2">
            <button
              type="button"
              onClick={() => onOpen(p)}
              aria-label={`Open ${p.part}`}
              style={{ color: accent, borderColor: accent }}
              className="press type-tiny shrink-0 w-7 h-7 grid place-items-center rounded-full border"
            >
              {p.part}
            </button>
            <ShowRest lines={4} accent={accent} className="min-w-0 flex-1">
              <ArabicText as="p" size="sm" className="block m-0 text-[var(--text-dim)]">
                {markedRuns(p.matn, p.marks).map((run, i) => {
                  if (!run.kind) return <span key={i}>{run.text} </span>
                  return (
                    <span key={i}>
                      <span
                        style={{ textDecorationColor: accent }}
                        className={`text-[var(--text)] underline underline-offset-4 decoration-2 ${run.kind === 'dots' ? 'decoration-dotted' : ''}`}
                      >
                        {run.text}
                      </span>
                      {run.other && <span className="type-tiny text-[var(--text-faint)]"> &asymp; {run.other}</span>}
                      {' '}
                    </span>
                  )
                })}
              </ArabicText>
            </ShowRest>
          </li>
        ))}
      </ul>
    </div>
  )
}
