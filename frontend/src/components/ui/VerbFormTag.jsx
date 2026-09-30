/**
 * Which bab (باب) a verb is, read from named dictionaries, never guessed from a
 * bare root. Sarf and Dictionary show the same fact through this one component.
 *
 * "No readings" is the never-guess surface: no source records this verb's bab,
 * and this line says so instead of looking like an answer. Two sources naming
 * the same bab already merge into one reading with both badges before this
 * ever renders; two readings here means the sources genuinely disagree, or
 * name two different verb forms off the same spelling.
 */
import ArabicText from './ArabicText'
import SourceBadge from './SourceBadge'

// The label reads "عَلِمَ · باب سَمِعَ يَسْمَعُ"; a reader who is already on the
// word wants only the pair that names the bab.
const babName = (label) => label.split('· باب ')[1] ?? label

/**
 * plain: only the bab names, side by side, for a card that already shows the
 * verb. Their sources stay out of sight until showSources is turned on.
 */
export default function VerbFormTag({ readings = [], plain = false, showSources = true }) {
  if (readings.length === 0) {
    return (
      <span data-testid="bab-readings" className="type-small text-[var(--text-faint)]">
        No dictionary here records this verb's باب.
      </span>
    )
  }

  if (plain) {
    return (
      <span data-testid="bab-readings" className="flex flex-wrap items-center gap-x-4 gap-y-1">
        {readings.map((reading) => (
          <span key={reading.label} className="inline-flex items-center gap-2 flex-wrap">
            <ArabicText size="sm" className="text-[var(--text-dim)]">{babName(reading.label)}</ArabicText>
            {showSources && reading.sources.map((source) => (
              <SourceBadge key={source.key} source={source} />
            ))}
          </span>
        ))}
      </span>
    )
  }

  return (
    <span data-testid="bab-readings" className="flex flex-col gap-1">
      {readings.map((reading) => (
        <span key={reading.label} className="inline-flex items-center gap-2 flex-wrap">
          <ArabicText size="sm" className="text-[var(--text-dim)]">{reading.label}</ArabicText>
          {reading.sources.map((source) => (
            <SourceBadge key={source.key} source={source} />
          ))}
        </span>
      ))}
    </span>
  )
}
