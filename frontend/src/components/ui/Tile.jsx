/**
 * The one tappable or standing box of Home: a tab's tile, a card for it, the big
 * "carry on" block. Look lives in styles/components.css (.tile, .tile-*).
 *
 * `variant`: 'row' a tab, 'lead' the block that carries on. `accent` is the tab's colour (--c).
 * A button unless `as` says otherwise.
 */
const VARIANT = {
  row: 'tile press min-h-11 space-y-1',
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
