/** The choice cards every level of the course list is drawn from. */
import { unitNumber } from '../../../lib/colloquial/place'
import ArabicText from '../../ui/ArabicText'
import SpeakButton from '../../ui/SpeakButton'
import { FOCUS } from '../parts/Face'
import PhrasePicture from '../parts/PhrasePicture'

// A choice card: its colour glows in from both ends and fades to nothing in the middle.
// Without onClick it is a unit or topic this dialect has not written yet: shown, not openable.
// With `twin` it is two halves joined, each its own way in: a topic's phrases and its words.
// `image` is a topic's first picture, a small square beside its words.
function Lines({ hue, kicker, title, gloss, arabic, note, more, image }) {
  return (
    <>
      {image && <PhrasePicture phrase={{ image }} alt="" className="float-end ms-3 w-12 h-12 rounded-[var(--radius-md)]" />}
      <span className="flex items-baseline justify-between gap-3">
        <span className="type-micro uppercase tracking-[0.18em]" style={{ color: hue }}>{kicker}</span>
        {arabic && <span lang="ar" dir="rtl" className="arabic-sm text-[var(--text-dim)]">{arabic}</span>}
      </span>
      <span className="block type-ui font-semibold text-[var(--text)] mt-1">{title}</span>
      {gloss && <i className="block type-small text-[var(--text-dim)]">{gloss}</i>}
      {note && <span className="block type-small text-[var(--text-faint)] mt-1">{note}</span>}
      {more && <span className="block mt-2">{more}</span>}
    </>
  )
}

const lookOf = (hue, index) => {
  const tint = (pct) => `color-mix(in oklab, ${hue} ${pct}%, transparent)`
  return {
    '--i': index,
    background: `linear-gradient(90deg, ${tint(26)}, transparent 38%, transparent 62%, ${tint(26)}), var(--surface)`,
    borderColor: tint(40),
  }
}

export function Card({ hue, index, onClick, twin, picture, ...lines }) {
  const look = lookOf(hue, index)
  const half = `lift press group text-start w-full px-5 py-4 ${FOCUS}`
  if (twin) {
    return (
      <div style={look} className="rise-in grid grid-cols-2 rounded-[var(--radius-lg)] border overflow-hidden">
        <button type="button" onClick={onClick} aria-label={`${lines.title}: ${lines.note}`} className={half}><Lines hue={hue} {...lines} /></button>
        <button type="button" onClick={twin.onClick} aria-label={`${lines.title}: ${twin.title} ${twin.kicker.toLowerCase()}`} className={`${half} border-s`} style={{ borderColor: look.borderColor }}>
          <Lines hue={hue} {...twin} />
        </button>
      </div>
    )
  }
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      style={look}
      className={`rise-in ${onClick ? 'lift press' : 'opacity-50 cursor-default'} group text-start w-full px-5 py-4 rounded-[var(--radius-lg)] border ${FOCUS} ${picture ? 'grid grid-cols-[1fr_auto] items-center gap-4' : ''}`}
    >
      {picture ? (
        // The Arabic name sits over the picture, so the English lines get the width.
        <>
          <span className="min-w-0"><Lines hue={hue} {...lines} arabic={null} /></span>
          <span className="flex flex-col items-end gap-1 self-stretch">
            <span lang="ar" dir="rtl" className="arabic-sm text-[var(--text-dim)]">{lines.arabic}</span>
            {picture}
          </span>
        </>
      ) : <Lines hue={hue} {...lines} />}
    </button>
  )
}

// A written unit opens on its cover phrase: said aloud, its picture filling the card's
// whole empty lower left, out to the border and across to the words, so no word sits
// on it. It takes the height the words make and never adds its own (contain: size).
// The speaker faces left, off the start of the Arabic. The whole card opens the unit; the speaker is
// drawn above that and only speaks, the words beside it letting a click through.
export function UnitCard({ hue, index, unit, onClick }) {
  const { cover } = unit
  const number = unitNumber(unit.unit)
  return (
    <div style={lookOf(hue, index)} className="rise-in lift press relative grid grid-rows-[auto_auto_1fr] px-5 py-4 rounded-[var(--radius-lg)] border">
      <button type="button" onClick={onClick} aria-label={`Unit ${number}: ${unit.title}`} className={`stretch absolute inset-0 rounded-[var(--radius-lg)] ${FOCUS}`} />
      <span className="flex items-baseline justify-between gap-3 type-micro uppercase tracking-[0.18em]">
        <span style={{ color: hue }}>Unit {number}</span>
        <span className="text-[var(--text-faint)]">{unit.lessons.length} topics</span>
      </span>
      <span className="type-ui font-semibold text-[var(--text)] mt-1">{unit.title}</span>
      <span className="flex gap-3.5 mt-2">
        <PhrasePicture phrase={cover} alt="" className="soft-edge pointer-events-none flex-1 min-w-0 [contain:size] -ms-5 -mb-4 rounded-es-[calc(var(--radius-lg)-1px)]" />
        <span className="relative pointer-events-none self-end flex flex-col items-end max-w-[70%]">
          <span className="flex items-center gap-2">
            <SpeakButton text={cover.arabic} className="pointer-events-auto -scale-x-100" />
            <ArabicText className="min-w-0 text-start [overflow-wrap:anywhere]">{cover.arabic}</ArabicText>
          </span>
          <span className="type-small text-[var(--text-faint)] text-end">{cover.english}</span>
        </span>
      </span>
    </div>
  )
}

export function Grid({ children }) {
  return <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">{children}</div>
}

