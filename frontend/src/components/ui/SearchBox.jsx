/**
 * The one box you type a question into.
 *
 * The Dictionary, Daleel and the Qur'an tab each ask for a word and each used
 * to draw their own field: the same label, the same clear button, the same
 * return key, written out three times and already drifting. One of the three
 * had a microphone beside it and the others did not. This is that field, once,
 * so a change to it lands on every tab at the same moment.
 *
 * It reads its direction off what has been typed rather than off a toggle above
 * it. A box that is empty runs left to right, so the faint placeholder always
 * starts in the same corner; the first Arabic letter turns the whole box round,
 * because that is the moment the writing itself changes direction. Nothing has
 * to be set before typing, and nothing is set wrongly.
 *
 * Clear and return sit at the end the writing runs away from, so they never
 * crowd the word being typed: on the far left under Arabic, the far right under
 * English. Reversing the row is what mirrors them, so there is one order to
 * read here rather than two lists of classes.
 *
 * A box with no onSubmit is a filter: it narrows a list as you type, so it
 * carries no return button (there is nothing to send) and Enter does nothing.
 * The clear button, the direction detection and the shell stay the same, which
 * is the point: a filter and a search should not look like two controls.
 *
 * Anything that belongs beside the box rather than inside it, a microphone,
 * goes in as children: the box's own edge already carries two controls and a
 * third in there would be a row of tiny targets.
 *
 * multiline swaps the input for a textarea in the same shell rather than a
 * second component: the label, hint, direction detection, clear button and
 * return button are one definition each tab shares. It starts one row tall,
 * the same height as every other tab's box, and grows only once a second
 * line is typed (field-sizing). Two fixed rows made the Nahw box look like a
 * different control.
 */
import ClearButton from './ClearButton'
import { isArabic } from '../../lib/arabicText'

export default function SearchBox({
  id,
  label,
  hint,
  placeholder,
  value,
  onChange,
  onSubmit,
  onClear,
  busy = false,
  disabled = false,
  accent,
  // For a box that only ever takes Arabic. Everywhere else the typing decides.
  arabic = false,
  // A sentence, not a word: Shift+Enter for a new line, and room to grow.
  multiline = false,
  children,
}) {
  const rtl = arabic || isArabic(value)
  const filtering = !onSubmit
  const ready = value.trim() && !disabled
  const Field = multiline ? 'textarea' : 'input'

  return (
    <div className="space-y-3">
      <label htmlFor={id} className="block text-sm font-medium text-[var(--text-dim)]">
        {label}
        {hint && (
          <span className="text-[var(--text-faint)] type-small font-normal ml-2">{hint}</span>
        )}
      </label>

      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Field
            id={id}
            {...(multiline ? { rows: 1 } : { type: 'text' })}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key !== 'Enter') return
              if (multiline && e.shiftKey) return
              if (filtering) return
              e.preventDefault()
              onSubmit()
            }}
            placeholder={placeholder}
            dir={rtl ? 'rtl' : 'ltr'}
            lang={rtl ? 'ar' : 'en'}
            style={{ '--c': accent }}
            className={`w-full rounded-[var(--radius-md)] p-4 bg-[var(--surface)]
              border border-[var(--border)] text-[var(--text)]
              placeholder:text-[var(--text-faint)] focus:border-[var(--c)]
              focus:outline-none transition-colors
              ${multiline ? 'resize-none max-h-48 [field-sizing:content]' : ''}
              ${rtl ? `arabic-lg text-right ${filtering ? 'pl-12' : 'pl-24'}` : filtering ? 'pr-12' : 'pr-24'}`}
          />

          <div
            className={`absolute top-1/2 -translate-y-1/2 flex items-center gap-1
              ${rtl ? 'left-3 flex-row-reverse' : 'right-3'}`}
          >
            {value && (
              /* ClearButton positions itself against the nearest positioned
                 parent, so it gets one of its own size rather than the field. */
              <span className="relative w-6 h-6 shrink-0">
                <ClearButton
                  label="Clear search"
                  className="inset-0"
                  onClick={() => (onClear ? onClear() : onChange(''))}
                />
              </span>
            )}
            {!filtering && (
            <button
              type="button"
              onClick={() => onSubmit()}
              disabled={busy || !ready}
              aria-label="Search"
              title="Search, or press Enter"
              style={{ background: ready ? accent : 'transparent' }}
              className={`w-8 h-8 grid place-items-center rounded-[var(--radius-sm)] shrink-0
                transition-[filter,background,color] duration-[calc(var(--motion-instant-ms)*1ms)]
                ${ready
                  ? 'text-[var(--bg)] hover:brightness-110'
                  : 'text-[var(--text-faint)] cursor-not-allowed'}`}
            >
              {busy ? (
                <span
                  aria-hidden="true"
                  className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"
                />
              ) : (
                /* The return key, drawn the way it is printed on a keyboard, so
                   the button and the hint above the field say the same thing. */
                <svg viewBox="0 0 16 16" className="w-4 h-4" fill="none" stroke="currentColor"
                  strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M14 3v4a2 2 0 0 1-2 2H3" />
                  <path d="M6 6 3 9l3 3" />
                </svg>
              )}
            </button>
            )}
          </div>
        </div>

        {children}
      </div>
    </div>
  )
}
