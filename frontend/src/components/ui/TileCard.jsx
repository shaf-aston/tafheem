/**
 * A tinted card that is one button: the look every timelines tile shares, the
 * home tiles, the compact row, and the event cards on the rail. Its hue comes
 * in as `hue` (0 to 360) and the tint is worked out in timelines.css, so the
 * card holds no colour of its own; `icon` is the faint picture behind the text.
 *
 * `variant` picks the size (tile, mini, event) and `index` staggers the entry.
 * `pressed` is for a row where one card is the current choice; `current` marks
 * the one a rail is reading.
 */
import TopicIcon from './TopicIcon'
import '../timelines.css'

export default function TileCard({
  hue, icon, variant = 'event', index = 0, pressed, current, label, className = '', onClick, children, ...rest
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      {...rest}
      aria-pressed={pressed}
      aria-current={current}
      aria-label={label}
      style={{ '--h': hue, '--i': index }}
      className={`tl-hue tl-card tl-${variant} lift press rise-in ${className}`.trim()}
    >
      <span className="tl-clip"><TopicIcon topic={icon} className="tl-ico" /></span>
      {children}
    </button>
  )
}
