/**
 * The one tappable or standing box of Home: a tab's tile, a card for it, the big
 * "carry on" block. Look lives in styles/components.css (.tile, .tile-*).
 *
 * `variant`: 'tab' a tab (tinted by its colour), 'chip' the same tile one line high
 * (All sections, the landing), 'lead' the block that carries on. `accent` is the tab's colour (--c).
 * A button unless `as` says otherwise.
 */
const VARIANT = {
  tab: 'tile tile-wash press rise-in min-h-[var(--layout-tile)] flex flex-col justify-start gap-2 text-left',
  chip: 'tile tile-wash tile-chip press rise-in flex items-center justify-between gap-2 min-h-11 text-left',
  lead: 'tile tile-lead rise-in space-y-3',
}

export default function Tile({ variant, accent, as: Tag = 'button', className = '', style, children, ...rest }) {
  return (
    <Tag
      {...(Tag === 'button' ? { type: 'button' } : {})}
      className={`${VARIANT[variant]} ${className}`.trim()}
      style={{ '--c': accent, ...style }}
      {...rest}
    >
      {children}
    </Tag>
  )
}
