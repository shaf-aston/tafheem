/**
 * The rest of a Maqayees entry with an English line for each Arabic line.
 *
 * `lines` is [{arabic, english}], cut and paired by the backend, which refuses
 * an answer it could not line up. These views never split anything again: a
 * second cut on the client is how English ends up under the wrong Arabic.
 *
 * Two ways to read the same pairs. LinePage prints the entry as the book does,
 * one flowing paragraph, and shows the English of whichever line you touch.
 * LineSpotlight takes one line at a time, English hidden until asked for.
 */
import { useCallback, useState } from 'react'

import { entryLines, VERSE_GAP } from '../lib/entryLines'
import { useRememberedFlag } from '../lib/useRemembered'

import { Line } from './EntryArabic'
import ArabicText from './ui/ArabicText'
import SmallButton from './ui/SmallButton'


/** Which line is current. Clamped at both ends, not wrapped: the entry has an end. */
function useLineCursor(count) {
  const [i, setI] = useState(0)
  const go = useCallback((n) => setI(Math.min(Math.max(n, 0), count - 1)), [count])
  const prev = () => go(i - 1)
  const next = () => go(i + 1)
  const onKeyDown = (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    if (e.key === 'ArrowLeft') prev(); else next()
  }
  return { i, go, prev, next, onKeyDown }
}

/** Two digits in Arabic-Indic figures, to sit among the Arabic. */
const arabicNumber = (n) => n.toLocaleString('ar-EG', { minimumIntegerDigits: 2, useGrouping: false })

const Gloss = ({ cursor, count, english }) => (
  <div className="flex items-start gap-3 pt-3 border-t border-[var(--border)]">
    <SmallButton aria-label="Previous line" disabled={cursor.i === 0} onClick={cursor.prev}>←</SmallButton>
    <div key={cursor.i} className="entry-rise flex-1 min-w-0 space-y-0.5" aria-live="polite">
      <div className="eyebrow">Line {cursor.i + 1} of {count}</div>
      <p className="type-body text-[var(--text)]" dir="ltr">{english}</p>
    </div>
    <SmallButton aria-label="Next line" disabled={cursor.i === count - 1} onClick={cursor.next}>→</SmallButton>
  </div>
)

export function LinePage({ lines, accent }) {
  const cursor = useLineCursor(lines.length)

  return (
    <div className="space-y-3" style={{ '--c': accent }} onKeyDown={cursor.onKeyDown}>
      <div dir="rtl" className="arabic text-justify" role="group" aria-label="Lines of the entry">
        {lines.map((pair, n) => {
          const verse = pair.arabic.includes(VERSE_GAP)
          return (
            <span key={n}>
              <button
                type="button"
                aria-pressed={n === cursor.i}
                onClick={() => cursor.go(n)}
                className={`entry-seg ${verse ? 'entry-seg--verse' : ''}`}
              >
                <sup className="type-tiny" aria-hidden="true">{arabicNumber(n + 1)}</sup>
                {verse
                  ? <Line line={entryLines(pair.arabic)[0]} />
                  : <ArabicText>{pair.arabic}</ArabicText>}
              </button>{' '}
            </span>
          )
        })}
      </div>
      <Gloss cursor={cursor} count={lines.length} english={lines[cursor.i].english} />
    </div>
  )
}

export function LineSpotlight({ lines, accent }) {
  const cursor = useLineCursor(lines.length)
  const { i } = cursor
  const [tryFirst, setTryFirst] = useRememberedFlag('dict.lines-try-first', true)
  // The line whose English was pressed. Moving on leaves it behind, so the
  // next line starts hidden again without anything to reset.
  const [shownAt, setShownAt] = useState(-1)
  const hidden = tryFirst && shownAt !== i

  return (
    <div className="space-y-3" style={{ '--c': accent }} onKeyDown={cursor.onKeyDown}>
      <label className="type-small text-[var(--text-dim)] flex items-center justify-end gap-2">
        <input
          type="checkbox"
          checked={tryFirst}
          onChange={(e) => setTryFirst(e.target.checked)}
          style={{ accentColor: accent }}
        />
        Try it first, then show the English
      </label>

      <div className="flex gap-0.5">
        {lines.map((_, n) => (
          <button
            key={n}
            type="button"
            aria-label={`Line ${n + 1}`}
            onClick={() => cursor.go(n)}
            className="h-2 flex-1 rounded-full"
            style={{
              background: n === i
                ? 'var(--c)'
                : n < i ? 'color-mix(in srgb, var(--c) 40%, transparent)' : 'var(--border)',
            }}
          />
        ))}
      </div>

      <div className="py-4 space-y-3 text-center">
        <Line line={entryLines(lines[i].arabic)[0]} size="lg" />
        <button
          type="button"
          className="entry-english type-body"
          data-hidden={hidden}
          aria-label={hidden ? 'Show the English' : undefined}
          disabled={!hidden}
          onClick={() => setShownAt(i)}
          dir="ltr"
        >
          {lines[i].english}
        </button>
      </div>

      <div className="flex items-center justify-between gap-3">
        <SmallButton disabled={i === 0} onClick={cursor.prev}>← Back</SmallButton>
        <span className="type-small text-[var(--text-faint)] tabular-nums">{i + 1} of {lines.length}</span>
        <SmallButton disabled={i === lines.length - 1} onClick={cursor.next}>Next →</SmallButton>
      </div>
    </div>
  )
}
