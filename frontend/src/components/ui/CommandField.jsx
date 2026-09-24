/**
 * The box you type a command into. One of these, used in both places.
 *
 * The header bar and the launcher behind the pen ask the same questions and
 * already share the same brain, useCommandLine. This is the rest of it: the
 * magnifying glass, the grey completion printed ahead of the cursor, and the
 * box itself. Written twice they drifted, and the launcher ended up a bare
 * underline with no glass and no completion, so the same typing behaved
 * differently depending on which one you opened.
 *
 * It takes the whole line object rather than a dozen loose props, because what
 * a caller wants is "put the command line here", not to wire a combobox up by
 * hand. What is left for the caller to choose is only what genuinely differs:
 * the words in an empty box, and whatever sits at the right-hand end, which in
 * the header is the Ctrl K badge and in the launcher is nothing.
 */
import { rowId } from '../../lib/commandRoutes'

export default function CommandField({
  line, name, inputRef, placeholder, onFocus, showing = false, trailing = null,
}) {
  return (
    <div className="cb-field">
      <svg className="cb-glass" viewBox="0 0 24 24" width="14" height="14" fill="none"
        stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" />
        <path d="M20 20l-3.5-3.5" />
      </svg>

      {/* The ghost sits under the real box, printing what was typed in nothing
          so the completion lands exactly where the next letter would. */}
      <span className="cb-ghost" aria-hidden="true">
        <span className="cb-ghost-typed">{line.query}</span>{line.ghost}
      </span>

      <input
        ref={inputRef}
        type="text"
        value={line.query}
        onChange={(e) => line.type(e.target.value)}
        onFocus={onFocus}
        onKeyDown={line.onKeyDown}
        className="cb-input"
        placeholder={placeholder}
        aria-label="Search, or type / for a tab, @ for a root, or an ayah like 2:255"
        role="combobox"
        aria-expanded={showing}
        aria-controls={`${name}-results`}
        // Focus never leaves this box while the arrows walk the list, so
        // pointing at the row by id is the only way a screen reader can say
        // which one is under the cursor.
        aria-activedescendant={showing ? rowId(name, line.active) : undefined}
        autoComplete="off"
        spellCheck="false"
      />

      {trailing}
    </div>
  )
}
