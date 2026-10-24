import { gradeGrid, rowName } from '../../../lib/nahw/tamreen'

import ArabicText from '../../ui/ArabicText'
import { MARK_LABEL, STATUS_CLASS } from './marks'
import OptionText from './OptionText'
import RedDot from './RedDot'

// One grid part: a row per word asked about, a chip per ruling.
export default function GridPart({ part, picks, onToggle, checked }) {
  const graded = checked ? gradeGrid(part, picks) : null
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <tbody>
          {part.rows.map((row) => {
            const rowGraded = graded?.rows.find((r) => r.row === row)
            return (
              <tr key={row} className="border-t border-[var(--border)]">
                {/* Allowed to wrap: a tarkeeb row names a whole phrase, and held on one line it pushed the choices off a phone. */}
                <th className="text-right font-normal py-2 pr-3 w-1/3 sm:w-auto">
                  <ArabicText size="lg">{rowName(part, row)}</ArabicText>
                </th>
                <td className="py-2">
                  <div className="flex flex-wrap gap-1.5">
                    {part.options.map((option) => {
                      const status = rowGraded ? rowGraded.options.find((o) => o.option === option).status : ''
                      const isPicked = (picks[row] ?? []).includes(option)
                      return (
                        <button
                          key={option}
                          type="button"
                          disabled={checked}
                          onClick={() => onToggle(row, option)}
                          aria-pressed={isPicked}
                          aria-label={checked && status ? `${option}: ${MARK_LABEL[status]}` : option}
                          className={`option inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border
                            ${checked ? STATUS_CLASS[status]
                              : isPicked ? 'border-[var(--primary)] text-[var(--primary-hi)]' : 'border-[var(--border)] text-[var(--text-dim)]'}`}
                        >
                          {checked && (status === 'bad' || status === 'miss') && <RedDot />}
                          <OptionText part={part} option={option} />
                        </button>
                      )
                    })}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
