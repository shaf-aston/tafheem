/**
 * The one big thing on Home: carry on where you stopped, or (first visit) begin.
 * Same card either way; `value` is the word you were on, absent on a first visit.
 */
import { isArabic } from '../../lib/text/arabicText'
import ArabicText from '../ui/ArabicText'
import PrimaryButton from '../ui/PrimaryButton'
import Tile from '../ui/Tile'

export default function ResumeCard({ tab, accent, value, label, goLabel, progressText, onGo }) {
  const shown = tab.place ? tab.place(value) : value
  return (
    <section aria-label={label} className="space-y-2">
      <h3 className="eyebrow eyebrow-lg">{label}</h3>
      <Tile as="div" variant="lead" accent={accent}>
        <div className="flex items-center gap-3">
          <ArabicText size="lg" style={{ color: accent }}>{tab.arabic}</ArabicText>
          <div className="min-w-0">
            <p className="font-semibold">{tab.label}</p>
            {shown && isArabic(shown)
              ? <ArabicText size="sm" className="block text-start text-[var(--text-dim)]">{shown}</ArabicText>
              : <p className="type-small text-[var(--text-dim)]" dir="auto">{shown ?? tab.blurb}</p>}
          </div>
        </div>
        {progressText && <p className="type-small tabular-nums text-[var(--text-faint)]">{progressText}</p>}
        <PrimaryButton accent={accent} onClick={() => onGo(tab.id, value ?? undefined)}>{goLabel} →</PrimaryButton>
      </Tile>
    </section>
  )
}
