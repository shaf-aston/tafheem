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
 * `title` is a hover note on the whole control.
 *
 * `fill` spreads the choices across the full width, equally, for a row that is
 * the main switch of a screen (log in or sign up) rather than a small filter.
 */
import { useMedia, PHONE } from '../../lib/hooks/useMedia'

export default function Segmented({
  label, options, value, onChange, accent, captioned = false, wrap = false, fill = false, compact = false, className = '', title,
}) {
  // A pill is the right shape for a row that stays one row. Where there are
  // enough choices to spill onto a second line, a pill's ends curve around two
  // rows at once and the control reads as a blob, so those rows square off.
  // On a phone every row may wrap: five choices at 390px clipped instead; its choices then
  // share each row's spare room, so a choice pushed to a second row does not sit alone at the left.
  // Each starts at its own word's width (grow, not flex-1): from zero, with a touch screen's
  // 44px floor (.tap) standing in for "no narrower than my word", every row "fit" and the words overlapped.
  const phone = useMedia(PHONE)
  const shape = wrap || phone ? 'flex-wrap rounded-2xl' : 'rounded-full'
  const row = (
    <div
      className={`flex gap-0.5 p-0.5 ${shape} bg-[var(--surface)] border border-[var(--border)] ${className}`}
      role="group"
      aria-label={label}
      title={captioned ? undefined : title}
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
            className={`press tap inline-flex items-center ${phone && !compact ? 'grow justify-center' : ''} ${fill ? 'flex-1 justify-center py-2.5' : compact ? 'px-3 py-1.5' : 'px-3.5 py-1.5'} rounded-full ${compact ? 'type-label' : 'type-ui'} font-medium transition-colors ${
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
    <div className="flex items-center gap-2" title={title}>
      <span className="eyebrow">{label}</span>
      {row}
    </div>
  )
}
