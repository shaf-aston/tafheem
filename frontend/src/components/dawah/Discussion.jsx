import ShowRest from '../ui/ShowRest'
import TimelineRefs from '../TimelineRefs'

// The long answer under the points: a few paragraphs, each with its own evidence,
// cut to a snippet so the short answer and the reasoning stay the first read.
export default function Discussion({ parts, library, accent, copy, onGo }) {
  return (
    <div className="space-y-3">
      <p className="type-small font-medium text-[var(--text-dim)]">{copy.depth}</p>
      <ShowRest lines={6} accent={accent} more={copy['depth-more']} less={copy['depth-less']}>
        <div className="space-y-4">
          {parts.map(part => (
            <div key={part.text} className="space-y-1.5">
              <p className="text-[var(--text-dim)] leading-relaxed">{part.text}</p>
              <div className="flex flex-wrap items-center gap-1.5 type-small">
                <em className="text-[var(--text-faint)]">{copy.evidence}</em>
                <TimelineRefs refs={part.refs || []} library={library} accent={accent} onGo={onGo} className="contents" />
                {part.note && <em className="text-[var(--text-faint)]">{part.note}</em>}
              </div>
            </div>
          ))}
        </div>
      </ShowRest>
    </div>
  )
}
