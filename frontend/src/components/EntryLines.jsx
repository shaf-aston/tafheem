/**
 * The rest of a Maqayees entry with an English line for each Arabic line.
 *
 * `lines` is [{arabic, english}], cut and paired by the backend, which refuses
 * an answer it could not line up. These views never split anything again: a
 * second cut on the client is how English ends up under the wrong Arabic.
 *
 * Two ways to read the same pairs. LinePage gives every line its own row with
 * its English under it (a tick box hides the English until a line is tapped).
 * LineSpotlight takes one line at a time, English hidden until asked for.
 */
import { useCallback, useState } from 'react'

import { entryLines, VERSE_GAP } from '../lib/entryLines'
import { useRememberedFlag } from '../lib/useRemembered'

import { Line } from './EntryArabic'
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

/** A quiet tick box above a view, for how it reads; the choice is remembered. */
const Tick = ({ checked, onChange, accent, children }) => (
  <label className="type-small text-[var(--text-dim)] flex items-center justify-end gap-2">
    <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} style={{ accentColor: accent }} />
    {children}
  </label>
)

export function LinePage({ lines, accent }) {
  const [tapToShow, setTapToShow] = useRememberedFlag('dict.lines-tap', false)
  const [open, setOpen] = useState(() => new Set())
  const toggle = (n) => setOpen((was) => {
    const now = new Set(was)
    if (!now.delete(n)) now.add(n)
    return now
  })

  return (
    <div className="space-y-2" style={{ '--c': accent }}>
      <Tick checked={tapToShow} onChange={setTapToShow} accent={accent}>Tap a line for its English</Tick>
      <div role="list" aria-label="Lines of the entry">
        {lines.map((pair, n) => {
          const shown = !tapToShow || open.has(n)
          const tap = tapToShow && {
            role: 'button',
            tabIndex: 0,
            'aria-expanded': shown,
            onClick: () => toggle(n),
            onKeyDown: (e) => {
              if (e.key !== 'Enter' && e.key !== ' ') return
              e.preventDefault()
              toggle(n)
            },
          }
          return (
            <div key={n} role="listitem" className="entry-row">
              <div className="entry-row-body" {...tap}>
                <span className="entry-num type-tiny" aria-hidden="true">{arabicNumber(n + 1)}</span>
                <div className="flex-1 min-w-0 space-y-0.5">
                  <Line line={entryLines(pair.arabic)[0]} />
                  {shown && (
                    <p dir="ltr" className={`type-body text-[var(--text-dim)] ${tapToShow ? 'entry-rise' : ''}`}>
                      {pair.english}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
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
      <Tick checked={tryFirst} onChange={setTryFirst} accent={accent}>Try it first, then show the English</Tick>

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
