/**
 * The row of tabs under the header. Draws the registry, decides nothing:
 * which tab is active and what switching does belong to the caller.
 */
import ArabicText from './ArabicText'

// A tab's `row` tier (see tabs.js) → when it shows. The open tab always shows.
const ROW_CLASS = { 1: '', 2: 'hidden md:block', 3: 'hidden' }

export default function TabStrip({ tabs, active, colorOf, onSelect, onAll }) {
  return (
    // No overflow here on purpose: setting one axis to auto makes the other
    // auto too, and the 1px underline below the strip would then raise a
    // scrollbar. Tabs past what fits are hidden by `row` and live in All
    // sections; wrap is only the fallback.
    //
    // The labels are type-body, the same size as the English being read
    // in the panels below.
    <div className="flex flex-wrap gap-0.5 sm:gap-1" role="tablist" aria-label="Tools">
      {tabs.map((tab, i) => {
        const selected = active === tab.id
        const tabAccent = colorOf(tab.id)
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={selected}
            aria-controls="tabpanel"
            onClick={() => onSelect(tab.id)}
            title={`${tab.label} (press ${i + 1})`}
            style={{
              '--c': tabAccent,
              color: selected ? tabAccent : undefined,
              // Every tab starts from no width and grows into its share,
              // so a half tab really is half of a whole one.
              flex: tab.half ? '0.5 1 0' : '1 1 0',
            }}
            className={`tab-btn relative ${selected ? '' : ROW_CLASS[tab.row]} ${tab.half ? 'min-w-[3rem] sm:min-w-[3.5rem]' : 'min-w-[4.5rem] sm:min-w-[5.5rem]'}
              py-1.5 px-0.5 sm:px-2 type-body font-medium ${selected ? '' : 'tab-idle'}`}
          >
            <span className="sm:hidden">{tab.short}</span>
            <span className="hidden sm:inline">{tab.label}</span>
            {/* Sized by .arabic alone. A size class here does nothing,
                .arabic already sets one and wins, so adding one only
                looks like it works while shrinking nothing, or shrinks
                this label away from every other Arabic word on screen. */}
            {/* Waits for xl: English + Arabic together crowd below that. */}
            <ArabicText className="text-[var(--text-faint)] ml-1.5 hidden xl:inline">
              {tab.arabic}
            </ArabicText>
            {/* The lit underline. Its glow is the shared .glow utility, the
                same recipe as every other glow in the app, not one of its own. */}
            <span
              aria-hidden="true"
              className={`tab-line absolute inset-x-1 -bottom-px h-0.5 rounded-full ${selected ? 'glow' : ''}`}
              style={{ background: selected ? tabAccent : 'transparent' }}
            />
          </button>
        )
      })}
      <button
        type="button"
        onClick={onAll}
        title="All sections"
        aria-label="All sections"
        aria-haspopup="dialog"
        className="tab-btn px-2 sm:px-3 text-[var(--text-faint)] hover:text-[var(--text)]"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
        </svg>
      </button>
    </div>
  )
}
