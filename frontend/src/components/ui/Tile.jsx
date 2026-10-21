/**
 * The one tappable or standing box of Home: a tab's tile, a card for it, the big
 * "carry on" block. Look lives in styles/components.css (.tile, .tile-*).
 *
 * `variant`: 'tab' a tab (tinted by its colour), 'chip' the same tile one line high
 * (All sections, the landing), 'lead' the block that carries on. `accent` is the tab's colour (--c).
 * Tab tiles are the grid under the lead block, often below the fold, so they .reveal
 * on scroll and lean to the mouse (.tilt); chip and lead are on screen at once and
 * keep .rise-in. All three stand at elevation e1.
 * A button unless `as` says otherwise.
 */
import { useTilt } from '../../lib/useTilt'
import { useReveal } from '../../lib/useReveal'

const VARIANT = {
  tab: 'tile tile-wash e1 tilt press min-h-[var(--layout-tile)] flex flex-col justify-start gap-2 text-left',
  chip: 'tile tile-wash tile-chip e1 press rise-in flex items-center justify-between gap-2 min-h-11 text-left',
  lead: 'tile tile-lead e1 rise-in space-y-3',
}

export default function Tile({ variant, accent, as: Tag = 'button', className = '', style, children, ...rest }) {
  const [ref, reveal] = useReveal()
  const tilt = useTilt()
  const tab = variant === 'tab'
  return (
    <Tag
      {...(Tag === 'button' ? { type: 'button' } : {})}
      {...(tab ? { ref, ...tilt } : {})}
      className={`${VARIANT[variant]} ${tab ? reveal : ''} ${className}`.trim()}
      style={{ '--c': accent, ...style }}
      {...rest}
    >
      {children}
    </Tag>
  )
}
