import ArabicText from '../ui/ArabicText'

// One topic on the home grid: how many questions it holds, its name and what it covers.
export default function TopicTile({ topic, index, selected, accent, onPick }) {
  return (
    <button
      type="button"
      onClick={() => onPick(topic)}
      aria-pressed={selected}
      style={{
        '--i': index,
        borderColor: selected ? accent : undefined,
        background: selected ? `color-mix(in srgb, ${accent} 12%, var(--surface))` : undefined,
      }}
      className="rise-in lift press text-left rounded-[var(--radius-md)] border border-[var(--border)]
        bg-[var(--surface)] p-4 flex flex-col gap-2 hover:border-[var(--c)]"
    >
      <span className="flex items-baseline justify-between gap-2">
        <span className="type-figure font-semibold" style={{ color: accent }}>{topic.questions.length}</span>
        <ArabicText size="sm" className="arabic-inline text-[var(--text-faint)]">{topic.arabic}</ArabicText>
      </span>
      <span className="font-semibold text-[var(--text)]">{topic.title}</span>
      <span className="type-small text-[var(--text-dim)] leading-snug">{topic.blurb}</span>
    </button>
  )
}
