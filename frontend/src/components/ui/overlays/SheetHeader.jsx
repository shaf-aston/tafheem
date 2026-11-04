/**
 * The top of a sheet: its title on the start side, the round ✕ on the end.
 *
 * Six sheets each built this row themselves, and two of them closed with a
 * "Close" text link where the rest had the ✕, so the same act looked different
 * from one sheet to the next. `className` replaces the padding, for a sheet
 * whose box already pads it; `align` is 'start' when the title runs to two
 * lines and the ✕ should stay by its first.
 */
import CloseButton from '../buttons/CloseButton'

export default function SheetHeader({ onClose, align = 'center', className = 'px-5 pt-4 pb-3', closeClassName = '', children }) {
  return (
    <header className={`flex ${align === 'start' ? 'items-start' : 'items-center'} justify-between gap-3 ${className}`}>
      <div className="min-w-0">{children}</div>
      <CloseButton onClick={onClose} className={`shrink-0 ${closeClassName}`.trim()} />
    </header>
  )
}
