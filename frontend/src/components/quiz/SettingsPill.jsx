/**
 * Settings chosen once and left, folded behind one pill that says what they
 * are (ui/Popover). Each child is a captioned ui/Segmented or ui/WheelPicker
 * row; the grid dissolves each row's own wrapper so every caption shares one
 * column and the rows start level. A phone folds more behind it than a wide
 * screen does: the tab decides what goes in.
 */
import Popover from '../ui/overlays/Popover'

export default function SettingsPill({ label, title, align, children }) {
  return (
    <Popover label={label} title={title} align={align}>
      <div className="grid grid-cols-[auto_auto] items-center gap-x-2 gap-y-2.5 [&>div]:contents">
        {children}
      </div>
    </Popover>
  )
}
