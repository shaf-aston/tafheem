/** One tab as a tile on Home: its Arabic name large in its own colour, its name under it. */
import ArabicText from '../ui/ArabicText'
import Tile from '../ui/Tile'

export default function JumpTile({ tab, accent, index, wide, onOpen }) {
  return (
    <Tile variant="jump" accent={accent} onClick={() => onOpen(tab.id)}
      className={wide ? 'col-span-2' : ''} style={{ '--i': index }}>
      <ArabicText size="lg" className="leading-tight" style={{ color: accent }}>{tab.arabic}</ArabicText>
      <span className="flex items-center gap-2 font-semibold type-ui">
        <span aria-hidden="true" className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: accent }} />
        {tab.label}
      </span>
    </Tile>
  )
}
