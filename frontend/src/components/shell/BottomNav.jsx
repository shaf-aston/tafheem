/**
 * The phone's tab bar: the reader's dock (lib/dock.js) plus More, pinned where the
 * thumb rests. Phones only; a wider screen keeps the TabStrip in the header.
 * Draws the registry, decides nothing, like TabStrip.
 */
import { ahead } from '../../lib/warm'

import MoreIcon from '../ui/MoreIcon'
import TabMark from '../ui/TabMark'

export default function BottomNav({ tabs, dock: ids, active, colorOf, onSelect, onAll, onHover }) {
  const dock = ids.map((id) => tabs.find((tab) => tab.id === id))
  // A tab not on the bar lights More, so the bar always says where you are.
  const elsewhere = !dock.some((tab) => tab.id === active)
  const here = elsewhere && tabs.find((tab) => tab.id === active)
  const item = 'tap flex-1 grid justify-items-center gap-0.5 pt-2 pb-1 type-tiny font-semibold'
  return (
    <nav className="bottom-nav sm:hidden fixed inset-x-0 bottom-0 z-[var(--layer-header)] flex" aria-label="Main">
      {dock.map((tab) => {
        const on = tab.id === active
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onSelect(tab.id)}
            {...ahead(() => onHover?.(tab.id))}
            aria-current={on ? 'page' : undefined}
            style={{ '--c': colorOf(tab.id) }}
            className={`${item} ${on ? 'text-[var(--c)]' : 'text-[var(--text-dim)]'}`}
          >
            <span className={`bottom-nav-mark ${on ? 'bottom-nav-on' : ''}`} aria-hidden="true"><TabMark tab={tab} /></span>
            {tab.short}
          </button>
        )
      })}
      <button
        type="button"
        onClick={onAll}
        aria-haspopup="dialog"
        aria-label={here ? `All sections, now on ${here.label}` : 'All sections'}
        aria-current={here ? 'page' : undefined}
        style={here ? { '--c': colorOf(active) } : undefined}
        className={`${item} ${elsewhere ? 'text-[var(--c)]' : 'text-[var(--text-dim)]'}`}
      >
        <span className={`bottom-nav-mark ${elsewhere ? 'bottom-nav-on' : ''}`} aria-hidden="true">
          <MoreIcon />
        </span>
        {here ? here.short : 'More'}
      </button>
    </nav>
  )
}
