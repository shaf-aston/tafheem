/**
 * The row of tabs under the header. Draws the registry, decides nothing:
 * which tab is active and what switching does belong to the caller.
 */
import ArabicText from './ArabicText'

export default function TabStrip({ tabs, active, colorOf, onSelect }) {
  return (
    // No overflow here on purpose: setting one axis to auto makes the other
    // auto too, and the 1px underline below the strip would then raise a
    // scrollbar. It wraps instead. Seven labels never did fit across a
    // phone on one line, they printed over each other from 430px down;
    // below that the strip becomes two tidy rows and every label stays
    // readable, and from 520px up it is the single row it always was.
    //
    // The labels are type-body, the same size as the English being read
    // in the panels below. They were a size of their own before, larger
    // than everything else on the page for no reason anyone could name.
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
            className={`tab-btn relative ${tab.half ? 'min-w-[3rem] sm:min-w-[3.5rem]' : 'min-w-[4.5rem] sm:min-w-[5.5rem]'}
              py-1.5 px-0.5 sm:px-2 type-body font-medium ${selected ? '' : 'tab-idle'}`}
          >
            <span className="sm:hidden">{tab.short}</span>
            <span className="hidden sm:inline">{tab.label}</span>
            {/* Sized by .arabic alone. A size class here does nothing,
                .arabic already sets one and wins, so adding one only
                looks like it works while shrinking nothing, or shrinks
                this label away from every other Arabic word on screen. */}
            {/* Waits for xl. With eight tabs the English and Arabic
                labels together ran into each other up to about 1100px. */}
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
    </div>
  )
}
