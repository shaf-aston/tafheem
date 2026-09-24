/**
 * Says where an answer came from, and how far it can be trusted.
 *
 * Every panel shows one. Grammar checked by a person, a fixed rule table, and a
 * language model having a guess all look equally confident on a screen, this is
 * the only thing that tells them apart, so it is never optional and never hidden
 * behind a hover. The wording comes from the backend, which reads it from
 * data/sources.json; nothing here decides what a source is called.
 */
import { levelOf } from '../../lib/confidence'

export default function SourceBadge({ source, className = '' }) {
  if (!source) return null
  const level = levelOf(source)

  // The label alone: "AI explanation" or "Saheeh International" already says
  // what made it. The level rides in the dot colour, and in hidden text for a
  // screen reader, which cannot see the colour. "A guess, can be wrong" beside
  // every AI answer was the same warning printed on every page.
  return (
    <span
      className={`inline-flex items-center gap-1.5 type-small leading-none
        px-2 py-1 rounded-full border ${className}`}
      style={{ color: level.color, borderColor: 'var(--border)' }}
      title={source.detail}
    >
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0"
        style={{ background: level.color }}
        aria-hidden="true"
      />
      {/* select-none keeps the hidden level out of a drag-select: without it,
          "Checked by a person, " rode along into the clipboard. */}
      <span className="sr-only select-none">{level.say}, </span>
      <span>{source.label}</span>
    </span>
  )
}
