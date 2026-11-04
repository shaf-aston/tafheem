/**
 * One tab on Home, the one tile every section wears: its Arabic name large in its
 * own colour, its name under it, what you do there (tablet up) and your progress.
 */
import ArabicText from '../ui/text/ArabicText'
import Tile from '../ui/display/Tile'

export default function ModuleCard({ tab, accent, index, progressText, onOpen }) {
  return (
    <Tile variant="tab" accent={accent} onClick={() => onOpen(tab.id)} style={{ '--i': index }}>
      <ArabicText size="lg" className="leading-tight" style={{ color: accent }}>{tab.arabic}</ArabicText>
      <span className="space-y-1">
        <span className="flex items-center gap-2 font-semibold type-ui">
          <span aria-hidden="true" className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: accent }} />
          {tab.label}
        </span>
        <span className="hidden sm:block type-small text-[var(--text-dim)]">{tab.blurb}</span>
        {progressText && <span className="block type-small tabular-nums text-[var(--text-faint)]">{progressText}</span>}
      </span>
    </Tile>
  )
}
