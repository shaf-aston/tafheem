/**
 * The dock along the bottom while you recite: the microphone, what it is
 * hearing, how far through the page you are, and help when you are stuck.
 *
 * It holds no rules. Every state on it was decided by lib/follow.js; this only
 * says what each one looks like, and the colours are the app's own tokens so
 * orange here is the orange everywhere else in the app.
 *
 * The microphone is the one big thing on it, because starting is the one thing
 * this screen is for. Everything else is quieter and sits around it.
 */
import { CHECK, MISSED, SAID, WRONG } from '../../lib/follow'
import { LOOK, verdictOf } from '../../lib/reciteColors'

import ArabicText from '../ui/ArabicText'
import Chip from '../ui/Chip'
import MicMark from '../ui/MicMark'

export default function ReciteStrip({ listening, problem, heard, marks, lines, accent, status, help, onStart, onStop, onStartAt }) {
  const tally = { [SAID]: 0, [CHECK]: 0, [WRONG]: 0, [MISSED]: 0 }
  for (const word of marks.words) if (word.state in tally) tally[word.state] += 1
  const live = accent || 'var(--primary)'

  return (
    <div
      className="reader-dock mt-2 rounded-[var(--radius-lg)] border border-[var(--border)]
        bg-[var(--surface)]/95 backdrop-blur p-3 sm:p-4 space-y-3 shadow-[var(--shadow-pop)]"
    >
      <div className="flex items-center gap-3 sm:gap-4">
        <button
          type="button"
          onClick={listening ? onStop : onStart}
          aria-pressed={listening}
          aria-label={listening ? 'Stop reciting' : 'Start reciting'}
          title={listening ? 'Stop' : 'Start reciting'}
          style={{ backgroundColor: listening ? live : undefined, borderColor: live, color: listening ? 'white' : live }}
          className={`mic-host shrink-0 grid place-items-center w-14 h-14 rounded-full border-2 transition-colors
            focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[color:var(--c)]/30
            ${listening ? '' : 'hover:bg-[var(--surface-hi)]'}`}
        >
          <MicMark state={listening ? 'recording' : 'idle'} size={26} />
        </button>

        {/* What it is hearing this moment, or, before that, what to do. The
            last words only: the page above already shows everything. Sound in
            a room is not somebody reciting, so until enough of the page has
            been heard it says so in words. */}
        <div className="min-w-0 flex-1 space-y-0.5" aria-live="polite">
          <p className="type-body font-medium text-[var(--text)] truncate">
            {listening ? (marks.started ? 'Listening…' : 'Listening. Start from the top of the page.') : 'Press to start reciting'}
          </p>
          {listening && marks.started && heard.length > 0 ? (
            <ArabicText size="sm" className="text-[var(--text-faint)] truncate block" dir="rtl">
              {heard.slice(-6).join(' ')}
            </ArabicText>
          ) : (
            <p className="type-small text-[var(--text-faint)] truncate">{status}</p>
          )}
        </div>

        <div className="hidden sm:flex items-center gap-3 shrink-0 tabular-nums type-small">
          {Object.entries(tally).filter(([, n]) => n > 0).map(([state, n]) => (
            <span key={state} className="flex items-center gap-1.5" style={{ color: LOOK[state].colour }}>
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: LOOK[state].bar }} aria-hidden="true" />
              {n} {LOOK[state].label}
            </span>
          ))}
          {marks.extras.length > 0 && (
            <span style={{ color: 'var(--danger)' }}>{marks.extras.length} added</span>
          )}
        </div>
      </div>

      {/* One segment an ayah, settled at the pause, so a whole page is one
          glance: a progress bar that also says how each ayah went. Each is
          also a way in: pressed, reciting follows from that ayah. The press
          area is taller than the bar, for a thumb. */}
      <div className="flex gap-1" dir="rtl" role="list" aria-label="how each ayah went">
        {lines.map((line) => {
          const verdict = verdictOf(marks.words.slice(line.from, line.from + line.count).map((w) => w.state))
          return (
            <span key={line.label} role="listitem" className="flex" style={{ flexGrow: line.count, flexBasis: 0 }}>
              <button
                type="button"
                onClick={() => onStartAt?.(line.from)}
                aria-label={`Recite from ${line.label}: ${verdict ? LOOK[verdict].label : 'not reached yet'}`}
                title={`${line.label}: ${verdict ? LOOK[verdict].label : 'not reached yet'}`}
                className="press flex-1 py-2 -my-2"
              >
                <span
                  className="block h-1.5 rounded-full transition-colors"
                  style={{ backgroundColor: verdict ? LOOK[verdict].bar : 'var(--border)' }}
                />
              </button>
            </span>
          )
        })}
      </div>

      {help && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="type-small text-[var(--text-faint)]">Stuck?</span>
          {help.map(({ label, onClick }) => (
            <Chip key={label} accent={accent} onClick={onClick}>{label}</Chip>
          ))}
        </div>
      )}

      {problem && <p className="type-small text-[var(--danger)]">{problem}</p>}
    </div>
  )
}
