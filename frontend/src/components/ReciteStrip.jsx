/**
 * The strip along the bottom while you recite: the microphone, what it is
 * hearing, how strictly it is marking, and how each ayah went.
 *
 * It holds no rules. Every state on it was decided by lib/follow.js; this only
 * says what each one looks like, and the colours are the app's own tokens so
 * orange here is the orange everywhere else in the app.
 */
import { CHECK, MISSED, SAID, WRONG } from '../lib/follow'
import { LOOK, verdictOf } from '../lib/reciteColors'
import { SETTINGS, setSetting, useSetting } from '../lib/settings'

import ArabicText from './ui/ArabicText'
import Segmented from './ui/Segmented'

// The same three choices the Settings page offers, read from the one place
// they are written down rather than copied, so they can never drift apart.
const LEVELS = SETTINGS.find((one) => one.key === 'reciting-level').options

export default function ReciteStrip({ listening, problem, heard, marks, lines, accent, onStart, onStop }) {
  const level = useSetting('reciting-level')
  const tally = { [SAID]: 0, [CHECK]: 0, [WRONG]: 0, [MISSED]: 0 }
  for (const word of marks.words) if (word.state in tally) tally[word.state] += 1

  return (
    <div
      className="sticky bottom-0 z-10 -mx-1 mt-2 rounded-[var(--radius-lg)] border border-[var(--border)]
        bg-[var(--surface)]/95 backdrop-blur px-3 py-2 space-y-2"
    >
      <div className="flex items-center gap-3 flex-wrap">
        <button
          type="button"
          onClick={listening ? onStop : onStart}
          aria-pressed={listening}
          style={listening ? { backgroundColor: accent, borderColor: accent } : undefined}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors
            ${listening
              ? 'text-white border-transparent'
              : 'border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text)]'}`}
        >
          {listening ? 'Stop' : 'Start reciting'}
        </button>

        {/* What it is hearing this moment. The last words only: the page above
            already shows everything, and a wall of text here would be read
            instead of it. Until enough of the page has been heard, it says so
            in words: sound in a room is not somebody reciting, and the page
            stays unmarked until it is. */}
        <div className="min-w-0 flex-1">
          {listening && !marks.started ? (
            <span className="type-small text-[var(--text-faint)]">
              Listening. Start from the top of the page.
            </span>
          ) : (
            <ArabicText size="sm" className="text-[var(--text-faint)] truncate block" dir="rtl">
              {heard.slice(-6).join(' ')}
            </ArabicText>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0 tabular-nums type-small">
          {Object.entries(tally).filter(([, n]) => n > 0).map(([state, n]) => (
            <span key={state} style={{ color: LOOK[state].colour }}>
              {n} {LOOK[state].label}
            </span>
          ))}
          {marks.extras.length > 0 && (
            <span style={{ color: 'var(--danger)' }}>{marks.extras.length} added</span>
          )}
        </div>

        {/* How strictly to mark, here rather than only buried in Settings,
            because it is the one thing a reciter wants to change the moment a
            mark looks unfair. Changing it re-marks the page at once, including
            what has already been recited: the marks are worked out afresh on
            every render from sureness already gathered, so nothing is recorded
            or read again. It stays the app's one setting, written to the same
            place, so Settings and this agree without either being told. */}
        <Segmented
          label="Checking level"
          captioned
          options={LEVELS}
          value={level}
          onChange={(id) => setSetting('reciting-level', id)}
          accent={accent}
          className="shrink-0"
        />
      </div>

      {/* One pill an ayah, settled at the pause, so a whole page is one glance. */}
      <div className="flex items-center gap-1 flex-wrap" dir="rtl">
        {lines.map((line) => {
          const verdict = verdictOf(marks.words.slice(line.from, line.from + line.count).map((w) => w.state))
          return (
            <span
              key={line.label}
              title={`${line.label}: ${verdict ? LOOK[verdict].label : 'not reached yet'}`}
              className="px-2 py-0.5 rounded-full type-tiny border"
              style={{
                color: verdict ? LOOK[verdict].colour : 'var(--text-faint)',
                borderColor: verdict ? LOOK[verdict].colour : 'var(--border)',
              }}
            >
              {line.label}
            </span>
          )
        })}
      </div>

      {problem && <p className="type-tiny text-[var(--text-faint)]">{problem}</p>}
    </div>
  )
}
