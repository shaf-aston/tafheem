/**
 * One row of mutually exclusive choices, quiet until chosen.
 *
 * Shared on purpose: the quiz's settings and the sarf table's size control are
 * the same kind of choice, so they are the same control rather than two that
 * merely look alike.
 *
 * `label` names the row. It is normally read only by a screen reader, because
 * one row on its own is obvious from its choices. Pass `captioned` where several
 * rows sit side by side and you would otherwise have to work out what each is
 * for, then the same words are shown, rather than a second set written twice.
 *
 * `compact` is the size of a small button beside it (the Copy button), for a row that sits in a header.
 *
 * `fill` spreads the choices across the full width, equally, for a row that is
 * the main switch of a screen (log in or sign up) rather than a small filter.
 */
export default function Segmented({
  label, options, value, onChange, accent, captioned = false, wrap = false, fill = false, compact = false, className = '',
}) {
  // A pill is the right shape for a row that stays one row. Where there are
  // enough choices to spill onto a second line, a pill's ends curve around two
  // rows at once and the control reads as a blob, so those rows square off.
  const shape = wrap ? 'flex-wrap rounded-2xl' : 'rounded-full'
  const row = (
    <div
      className={`flex gap-0.5 p-0.5 ${shape} bg-[var(--surface)] border border-[var(--border)] ${className}`}
      role="group"
      aria-label={label}
    >
      {options.map((option) => {
        const on = value === option.id
        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onChange(option.id)}
            aria-pressed={on}
            style={on
              ? { color: accent, background: `color-mix(in srgb, ${accent} 16%, transparent)` }
              : undefined}
            className={`press tap inline-flex items-center ${fill ? 'flex-1 justify-center py-2.5' : compact ? 'px-3 py-1.5' : 'px-3.5 py-1.5'} rounded-full ${compact ? 'text-xs' : 'text-sm'} font-medium transition-colors ${
              on ? '' : 'text-[var(--text-faint)] hover:text-[var(--text-dim)]'
            }`}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )

  if (!captioned) return row

  return (
    <div className="flex items-center gap-2">
      <span className="eyebrow">{label}</span>
      {row}
    </div>
  )
}
