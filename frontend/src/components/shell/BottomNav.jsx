/**
 * The phone's tab bar: the reader's dock (lib/nav/dock.js) plus More, pinned where the
 * thumb rests. Phones only; a wider screen keeps the TabStrip in the header.
 * Draws the registry, decides nothing, like TabStrip. Holding the current tab
 * opens its jump fan (lib/jumpFan.js).
 */
import { JUMPS, useJumpFan } from '../../lib/shell/jumpFan'
import { ahead } from '../../lib/api/warm'

import MoreIcon from '../ui/display/MoreIcon'
import TabMark from './TabMark'

export default function BottomNav({ tabs, dock: ids, active, colorOf, onSelect, onAll, onHover }) {
  const dock = ids.map((id) => tabs.find((tab) => tab.id === id))
  // A tab not on the bar lights More, so the bar always says where you are.
  const elsewhere = !dock.some((tab) => tab.id === active)
  const here = elsewhere && tabs.find((tab) => tab.id === active)
  const { bind, fan, list, usable } = useJumpFan()
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
            {...(on ? bind : {})}
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
        {...(here ? bind : {})}
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
      {fan && (
        <div ref={list} className="jump-fan" style={{ left: `clamp(4rem, ${fan.x}px, calc(100vw - 4rem))`, '--c': colorOf(active) }} aria-hidden="true">
          {JUMPS.filter((jump) => usable(jump.id)).map((jump) => (
            <div key={jump.id} data-jump={jump.id} className={jump.id === fan.lit ? 'jump-fan-lit' : undefined}>{jump.label}</div>
          ))}
        </div>
      )}
    </nav>
  )
}
