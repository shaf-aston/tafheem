/**
 * The phone's tab bar: the `dock` tabs from tabs.js plus More, pinned where the
 * thumb rests. Phones only; a wider screen keeps the TabStrip in the header.
 * Draws the registry, decides nothing, like TabStrip.
 */
const MORE = 'M6 12h.01M12 12h.01M18 12h.01'

export default function BottomNav({ tabs, active, colorOf, onSelect, onAll, onHover }) {
  const dock = tabs.filter((tab) => tab.dock)
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
            onFocus={() => onHover?.(tab.id)}
            aria-current={on ? 'page' : undefined}
            style={{ '--c': colorOf(tab.id) }}
            className={`${item} ${on ? 'text-[var(--c)]' : 'text-[var(--text-dim)]'}`}
          >
            <span className={`bottom-nav-mark arabic-inline ${on ? 'bottom-nav-on' : ''}`} lang="ar" dir="rtl" aria-hidden="true">{tab.mark}</span>
            {tab.short}
          </button>
        )
      })}
      <button
        type="button"
        onClick={onAll}
        aria-haspopup="dialog"
        aria-current={here ? 'page' : undefined}
        style={here ? { '--c': colorOf(active) } : undefined}
        className={`${item} ${elsewhere ? 'text-[var(--c)]' : 'text-[var(--text-dim)]'}`}
      >
        <span className={`bottom-nav-mark ${elsewhere ? 'bottom-nav-on' : ''}`} aria-hidden="true">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d={MORE} /></svg>
        </span>
        {here ? here.short : 'More'}
      </button>
    </nav>
  )
}
