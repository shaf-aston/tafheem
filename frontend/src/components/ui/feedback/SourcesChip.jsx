/**
 * Where an answer came from, when more than one source made it: one chip, "Sources (3)", that opens
 * the list. A single source stays a plain SourceBadge, and so does none (nothing is drawn).
 *
 * The weakest level among them rides on the chip's dot, so a guess is never behind the fold: the chip
 * is as honest as its worst member. Opened, each source is its badge with the level spelled out
 * beside it ("Checked by a person", "A guess, can be wrong") and what the source says of itself.
 * Opening, Escape and the focus return are Popover's.
 */
import { CONFIDENCE, levelOf } from '../../../lib/text/confidence'
import Popover from '../overlays/Popover'
import SourceBadge from './SourceBadge'

// The levels from most to least sure, as CONFIDENCE names them; the chip wears the last one present.
const LEVELS = Object.keys(CONFIDENCE)
const weakest = (sources) => sources.reduce((worst, source) => (
  LEVELS.indexOf(source.confidence) === -1 || LEVELS.indexOf(source.confidence) > LEVELS.indexOf(worst.confidence) ? source : worst
))

/** The sources once each, in the order given: two badges with one key are one fact said twice. */
const distinct = (sources) => {
  const seen = new Set()
  return sources.filter((source) => {
    if (!source) return false
    const id = source.key ?? source.label
    if (seen.has(id)) return false
    seen.add(id)
    return true
  })
}

export default function SourcesChip({ sources = [], align = 'start', className = '' }) {
  const list = distinct(sources)
  if (list.length === 0) return null
  if (list.length === 1) return <SourceBadge source={list[0]} className={className} />
  const level = levelOf(weakest(list))
  return (
    <span className={`inline-flex ${className}`}>
      <Popover
        align={align}
        title="Where this came from"
        label={(
          <>
            <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: level.color }} aria-hidden="true" />
            <span className="sr-only select-none">{level.say}, </span>
            Sources ({list.length})
          </>
        )}
      >
        <ul className="space-y-2 m-0 p-0 list-none">
          {list.map((source) => (
            <li key={source.key ?? source.label} className="space-y-0.5">
              <div className="flex items-center gap-2 flex-wrap">
                <SourceBadge source={source} />
                <span aria-hidden="true" className="type-tiny text-[var(--text-faint)]">{levelOf(source).say}</span>
              </div>
              {source.detail && <p className="type-tiny text-[var(--text-dim)] m-0 max-w-[22rem]">{source.detail}</p>}
            </li>
          ))}
        </ul>
      </Popover>
    </span>
  )
}
