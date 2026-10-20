/** One tab on Home: its name in its own colour, what you do there (from a tablet up), and your progress in it. */
import ArabicText from '../ui/ArabicText'
import Tile from '../ui/Tile'

export default function ModuleCard({ tab, accent, progressText, onOpen }) {
  return (
    <Tile variant="row" accent={accent} onClick={() => onOpen(tab.id)}>
      <span className="flex items-baseline justify-between gap-2">
        <span className="font-bold" style={{ color: accent }}>{tab.label}</span>
        <ArabicText size="sm" className="text-[var(--text-faint)]">{tab.arabic}</ArabicText>
      </span>
      <span className="hidden sm:block type-small text-[var(--text-dim)]">{tab.blurb}</span>
      {progressText && <span className="block type-small tabular-nums text-[var(--text-faint)]">{progressText}</span>}
    </Tile>
  )
}
