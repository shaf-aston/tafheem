/** One tab as a tile on Home: its Arabic name large in its own colour, its name under it. */
import ArabicText from '../ui/ArabicText'

export default function JumpTile({ tab, accent, index, onOpen }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(tab.id)}
      className="press rise-in text-start relative overflow-hidden min-h-24 p-3 flex flex-col justify-between gap-2
        rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] hover:border-[var(--c)]
        transition-colors"
      style={{
        '--c': accent,
        '--i': index,
        backgroundImage: 'radial-gradient(90% 90% at 100% 0, color-mix(in srgb, var(--c) 22%, transparent), transparent 65%)',
      }}
    >
      <ArabicText size="lg" className="leading-tight" style={{ color: accent }}>{tab.arabic}</ArabicText>
      <span className="flex items-center gap-2 font-semibold type-ui">
        <span aria-hidden="true" className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: accent }} />
        {tab.label}
      </span>
    </button>
  )
}
