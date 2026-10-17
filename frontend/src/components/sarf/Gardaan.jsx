import { useState } from 'react'

import ArabicText from '../ui/ArabicText'
import Chip from '../ui/Chip'
import RetryButton from '../ui/RetryButton'
import WheelPicker from '../ui/WheelPicker'
import BlockTitle from './BlockTitle'
import { CONJUGATIONS } from './conjugations'
import SarfSagheer from './SarfSagheer'
import SlotHead from './SlotHead'
import TableNote from './TableNote'

// The book prints the four active columns together and keeps the passives for
// later, so the first four columns the server sends are what opens by default.
const DEFAULT_COLUMN_COUNT = 4

/**
 * The gardaan, laid out the way a madrasah book prints it: the fourteen persons
 * read down the side, each tense reads across. Seeing the pattern repeat is the
 * whole point, so nothing here is allowed to push the grid off the page; it
 * scrolls inside its own box and the person column stays pinned beside it.
 */
export default function Gardaan({ table, accent, form, options, onForm, swapPending, swapError, onRetrySwap }) {
  // table is null when no source names a باب yet: the picker below still
  // lets the reader choose one, it is only the grid that has nothing to show.
  const { columns = [], rows = [], summary = [], notes = [] } = table ?? {}
  const allIds = columns.map((c) => c.id)

  // A pick answers instantly in the UI even though the table itself is still
  // rebuilding on the server; without this the picker snaps back to the old
  // form until that swap resolves, which reads as the click having failed.
  const [picked, setPicked] = useState(form ?? '')
  const choose = (id) => { setPicked(id); onForm(id) }

  // A different baab can bring different columns, so the choice starts fresh
  // rather than pointing at columns that are no longer there. Reset while
  // rendering, the same way the input box follows an incoming root above; one
  // idiom for "this state follows that prop", not two.
  const signature = allIds.join('|')
  const [shown, setShown] = useState(() => allIds.slice(0, DEFAULT_COLUMN_COUNT))
  const [known, setKnown] = useState(signature)
  if (signature !== known) {
    setKnown(signature)
    setShown(allIds.slice(0, DEFAULT_COLUMN_COUNT))
  }

  const visible = columns.filter((c) => shown.includes(c.id))
  // Emptying the table entirely helps nobody, so the last column stays on.
  const toggle = (id) => setShown((prev) => (
    prev.includes(id)
      ? (prev.length > 1 ? prev.filter((x) => x !== id) : prev)
      : allIds.filter((x) => prev.includes(x) || x === id)
  ))

  return (
    <div className="space-y-4">
      {summary.length > 0 && <SarfSagheer summary={summary} accent={accent} />}

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <BlockTitle {...CONJUGATIONS} />
        {options && (
          <div className="flex items-center gap-2">
            {swapPending && (
              <span className="type-small text-[var(--text-faint)]">Rebuilding the table…</span>
            )}
            {/* No form chosen yet (no book records the باب): the control must not
                read as an answer, so it shows a prompt, never a form. */}
            <WheelPicker
              label="Verb form"
              placeholder="Choose a باب"
              options={Object.entries(options).map(([id, label]) => ({ id, label }))}
              value={picked || form}
              onChange={choose}
              disabled={swapPending}
              accent={accent}
              className="max-w-[14rem]"
            />
            {/* Beside the control that failed, not at the top of the page: the
                word's own answer above is still good, only the swap broke. */}
            {swapError && (
              <span className="flex items-center gap-1.5 type-small text-[var(--danger)]">
                {swapError}
                <RetryButton onClick={onRetrySwap} />
              </span>
            )}
          </div>
        )}
      </div>

      {table && (
        <>
          {/* Six columns at once is too wide for a laptop and unreadable on a phone,
              so the reader turns on only the ones being studied. */}
<div role="group" aria-label="Columns to show" dir="rtl" className="flex flex-wrap items-center gap-2">
            {columns.map((c) => (
              <Chip key={c.id} tinted accent={accent} selected={shown.includes(c.id)} onClick={() => toggle(c.id)}>
                {c.label}
              </Chip>
            ))}
          </div>

          {/* Arabic reads right to left, and so does the book's grid: ماضي sits on
              the right and نهي on the left. The direction lives on the scroll box so
              a table too wide for the screen opens at ماضي, not at the passives. */}
          <div
            dir="rtl"
            className={`rise-in overflow-x-auto rounded-[var(--radius-md)] border border-[var(--border)] transition-opacity ${
              swapPending ? 'opacity-50' : ''
            }`}
          >
            <table className="w-max min-w-full type-body border-collapse">
              <thead>
                <tr className="bg-[var(--surface-hi)]">
                  {visible.map((c) => (
                    <th key={c.id} className="px-4 py-2 text-center align-bottom font-normal">
                      <SlotHead label={c.label} term={c.arabic} />
                    </th>
                  ))}
                  {/* Last in an RTL row is the far left, which is where the one
                      English column belongs, out of the way of the Arabic. */}
                  <th
                    dir="ltr"
                    className="eyebrow font-normal sticky left-0 z-[var(--layer-raised)] bg-[var(--surface-hi)] text-left px-4 py-2"
                  >
                    Person
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={row.person} className={i % 2 ? 'bg-[var(--surface)]' : ''}>
                    {visible.map((c) => (
                      <td key={c.id} className="px-4 py-1.5 text-center whitespace-nowrap text-[var(--text)]" dir="rtl" lang="ar">
                        {/* Reading size, the same as the صرف صغير above; a verb is
                            the thing being studied here, not a label. */}
                        <ArabicText>{row.cells?.[c.id] ?? ''}</ArabicText>
                      </td>
                    ))}
                    <th
                      scope="row"
                      dir="ltr"
                      className={`sticky left-0 z-[var(--layer-raised)] px-4 py-1.5 text-left font-normal whitespace-nowrap
                        type-small text-[var(--text-dim)] ${i % 2 ? 'bg-[var(--surface)]' : 'bg-[var(--surface-hi)]'}`}
                    >
                      {row.person}
                    </th>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Some of the book's rules allow a second spelling. Choosing one of
              them silently would print a preference as if it were the rule, so
              the others are named under the table instead. */}
          {notes.length > 0 && (
            <TableNote accent={accent} title="The book also allows">
              {notes.join(' ')}
            </TableNote>
          )}
        </>
      )}
    </div>
  )
}
