import { recitedForm } from '../../lib/text/arabicText'
import { sameSpokenWord } from '../../lib/text/arabicText'

import ArabicText from '../ui/ArabicText'
import WheelPicker from '../ui/WheelPicker'

/** One missing word: a box to type into, and after checking, how it went. */
export default function Gap({ word, options, value, checked, accent, lineLabel, typeWidth, onChange }) {
  const right = checked && sameSpokenWord(value, word)
  const wrong = checked && !right
  const border = wrong ? 'var(--danger)' : right ? 'var(--success)' : 'var(--border)'
  const gapLabel = `missing word, ${lineLabel}`

  return (
    <span className="inline-flex flex-col items-center">
      {options ? (
        // The four words, on the app's one picker (ui/WheelPicker), drawn as a
        // blank in the line: a page can hold a dozen gaps, and four buttons
        // each would be a wall rather than a line of text to read. Every gap
        // is as wide as its own longest choice, so the row does not jump as
        // words are picked; sizing by the answer would give its length away.
        // Read-only after checking, so a marked answer keeps its focus ring.
        <span
          className="memorise-gap"
          style={{
            '--gap-border': border,
            '--gap-text': right || wrong ? border : undefined,
            width: `${Math.max(...options.map((o) => recitedForm(o).length)) + 5}ch`,
          }}
        >
          <WheelPicker
            label={gapLabel}
            placeholder="…"
            options={options.map((option) => ({ id: option, label: option }))}
            value={value}
            onChange={onChange}
            readOnly={checked}
            arabic
            accent={accent}
          />
        </span>
      ) : (
      <ArabicText
        as="input"
        size="lg"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        readOnly={checked}
        aria-label={gapLabel}
        style={{ '--gap-border': border, caretColor: accent, width: `${typeWidth}ch` }}
        className="bg-transparent border-b-2 text-center outline-none
          border-[color:var(--gap-border)] focus-visible:border-[color:var(--c)]
          focus-visible:ring-2 focus-visible:ring-[color:var(--c)]/40 focus-visible:outline-none
          transition-colors"
      />
      )}
      {/* The word itself, once the page is marked and only where it was missed.
          Showing it beside a right answer would just be printing it twice. */}
      {wrong && (
        <ArabicText size="sm" className="text-[var(--danger)]">{word}</ArabicText>
      )}
    </span>
  )
}
