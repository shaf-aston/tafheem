/** Above every level below the top: the way back up, and the same place in another dialect. */
import { colorFor } from '../../../theme'
import WheelPicker from '../../ui/WheelPicker'
import { FOCUS } from '../parts/Face'

// Where you are, each earlier step a button back to it.
export function Breadcrumbs({ steps }) {
  return (
    <nav aria-label="Where you are" className="flex flex-wrap items-center gap-x-2 gap-y-1 type-small">
      {steps.map((step, i) => {
        const last = i === steps.length - 1
        return (
          <span key={step.label} className="flex items-center gap-2">
            {i > 0 && <span aria-hidden className="text-[var(--text-faint)]">›</span>}
            {last
              ? <span aria-current="page" className="text-[var(--text)] font-medium">{step.label}</span>
              : <button type="button" onClick={step.go} className={`press text-[var(--text-dim)] hover:text-[var(--text)] underline-offset-4 hover:underline rounded ${FOCUS}`}>{step.label}</button>}
          </span>
        )
      })}
    </nav>
  )
}

// A quiet switch for learners who know more than one dialect: every dialect
// walks the same spine, so the same unit and topic are there to land on. A unit
// the other dialect has not written yet drops back to its unit list.
export function DialectSwitch({ dialects, current, onPick }) {
  return (
    <div className="ms-auto flex items-center gap-2 type-small text-[var(--text-faint)]">
      <span className="hidden sm:inline">Same place in</span>
      <WheelPicker label="Dialect" options={dialects.map((d) => ({ id: d.key, label: d.label }))}
        value={current} onChange={onPick} accent={colorFor('tab', 'colloq')} />
    </div>
  )
}

