import TimelineRefs from '../ui/text/TimelineRefs'

// The evidence under a claim: a label, its references, and a note where a reference does not fit.
export default function Evidence({ refs, note, library, accent, onGo, label }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 type-small">
      <em className="text-[var(--text-faint)]">{label}</em>
      <TimelineRefs refs={refs} library={library} accent={accent} onGo={onGo} className="contents" />
      {note && <em className="text-[var(--text-faint)]">{note}</em>}
    </div>
  )
}
