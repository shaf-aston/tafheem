/**
 * The phone's tab bar, pinned where the thumb rests: the reader's two docked tabs
 * (lib/nav/dock.js, Home and Qur'an until changed), Ask in the middle (one box for
 * any word, ayah or sentence), Learn (every other tab, the All sections sheet) and
 * Me (progress and account). Phones only; a wider screen keeps the TabStrip in the
 * header. Draws the registry, decides nothing, like TabStrip. Holding the current
 * tab opens its jump fan (lib/jumpFan.js).
 */
import { JUMPS, useJumpFan } from '../../lib/shell/jumpFan'
import { ahead } from '../../lib/api/warm'

import TabMark from './TabMark'

// Line pictures for the three bar places that are not tabs, drawn like the emblems.
const ICONS = {
  ask: ['M11 4.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13Z', 'm20 20-4.2-4.2'],
  learn: ['M12 21v-9', 'M12 12c0-4 3-7 8-7 0 4-3 7-8 7Z', 'M12 14c0-3-2.5-6-7-6 0 3.5 2.5 6 7 6Z'],
  me: ['M12 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z', 'M4.5 21c1-4 4-6 7.5-6s6.5 2 7.5 6'],
}
const Icon = ({ name, size = 22 }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {ICONS[name].map((d) => <path key={d} d={d} />)}
  </svg>
)

export default function BottomNav({ tabs, dock: ids, active, colorOf, onSelect, onAll, onAsk, onMe, onHover }) {
  const dock = ids.map((id) => tabs.find((tab) => tab.id === id))
  // A tab not on the bar lights More, so the bar always says where you are.
  const elsewhere = !dock.some((tab) => tab.id === active)
  const here = elsewhere && tabs.find((tab) => tab.id === active)
  const { bind, fan, list, usable } = useJumpFan()
  const item = 'tap flex-1 grid justify-items-center gap-0.5 pt-2 pb-1 type-tiny font-semibold'
  return (
    <nav className="bottom-nav sm:hidden fixed inset-x-0 bottom-0 z-[var(--layer-header)] flex" aria-label="Main">
      {/* One pill for the whole bar, gliding to the tab that is on rather than
          blinking out under one and in under the next. Drawn first, so the
          marks sit on top of it. Learn lights for every tab not on the bar. */}
      <span
        className="bottom-nav-pill"
        aria-hidden="true"
        style={{ '--at': elsewhere ? dock.length + 1 : dock.findIndex((tab) => tab.id === active), '--of': dock.length + 3, '--c': colorOf(active) }}
      />
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
      <button type="button" onClick={onAsk} aria-haspopup="dialog" aria-label="Ask: a word, root, ayah or sentence" className="tap flex-1 grid justify-items-center bottom-nav-ask">
        <span aria-hidden="true"><Icon name="ask" size={24} /></span>
      </button>
      <button
        type="button"
        onClick={onAll}
        {...(here ? bind : {})}
        aria-haspopup="dialog"
        aria-label={here ? `All sections, now on ${here.label}` : 'Learn: all sections'}
        aria-current={here ? 'page' : undefined}
        style={here ? { '--c': colorOf(active) } : undefined}
        className={`${item} ${elsewhere ? 'text-[var(--c)]' : 'text-[var(--text-dim)]'}`}
      >
        <span className={`bottom-nav-mark ${elsewhere ? 'bottom-nav-on' : ''}`} aria-hidden="true">
          {here ? <TabMark tab={here} /> : <Icon name="learn" />}
        </span>
        {here ? here.short : 'Learn'}
      </button>
      <button type="button" onClick={onMe} aria-haspopup="dialog" aria-label="Me: your progress and account" className={`${item} text-[var(--text-dim)]`}>
        <span className="bottom-nav-mark" aria-hidden="true"><Icon name="me" /></span>
        Me
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
