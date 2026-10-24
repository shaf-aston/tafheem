import ShowRest from '../ui/ShowRest'
import Evidence from './Evidence'
import knobs from '../../config/dawah.json'

// The long answer under the points: a few paragraphs, each with its own evidence,
// cut to a snippet so the short answer and the reasoning stay the first read.
export default function Discussion({ parts, library, accent, copy, onGo }) {
  return (
    <div className="space-y-3">
      <p className="type-small font-medium text-[var(--text-dim)]">{copy.depth}</p>
      <ShowRest lines={knobs['depth-lines']} accent={accent} more={copy['depth-more']} less={copy['depth-less']}>
        <div className="space-y-4">
          {parts.map(part => (
            <div key={part.text} className="space-y-1.5">
              <p className="text-[var(--text-dim)] leading-relaxed">{part.text}</p>
              <Evidence refs={part.refs || []} note={part.note} library={library} accent={accent} onGo={onGo} label={copy.evidence} />
            </div>
          ))}
        </div>
      </ShowRest>
    </div>
  )
}
