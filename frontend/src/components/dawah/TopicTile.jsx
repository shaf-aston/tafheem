import ArabicText from '../ui/ArabicText'
import { useFirstSight } from '../../lib/firstSight'

// One topic on the home grid: how many questions it holds, its name and what it covers.
export default function TopicTile({ topic, index, selected, onPick }) {
  const rise = useFirstSight(`dawah-topic:${topic.id}`)
  return (
    <button
      type="button"
      onClick={() => onPick(topic)}
      aria-pressed={selected}
      style={{
        '--i': index,
        borderColor: selected ? 'var(--c)' : undefined,
        background: selected ? 'color-mix(in srgb, var(--c) 12%, var(--surface))' : undefined,
      }}
      className={`${rise ? 'rise-in ' : ''}lift press text-left rounded-[var(--radius-md)] border border-[var(--border)]
        bg-[var(--surface)] p-4 flex flex-col gap-2 hover:border-[var(--c)]`}
    >
      <span className="flex items-baseline justify-between gap-2">
        {/* The ﷺ stays with the word before it, never alone on a line. */}
        <span className="font-semibold text-[var(--c)]">{topic.title.replace(/ (?=ﷺ$)/, '\u00a0')}</span>
        <ArabicText size="sm" className="arabic-inline text-[var(--text-faint)]">{topic.arabic}</ArabicText>
      </span>
      <span className="type-small text-[var(--text-dim)] leading-snug">{topic.blurb}</span>
    </button>
  )
}
