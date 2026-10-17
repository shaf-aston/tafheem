import { gradeRule } from '../../../lib/tamreen'

import { MARK_LABEL, STATUS_CLASS } from './marks'
import OptionText from './OptionText'
import RedDot from './RedDot'

// A tick-every-true list: a rule question, or one list part of an example.
export default function OptionList({ part, picked, onToggle, checked }) {
  const graded = checked ? gradeRule(part, picked) : null
  return (
    <div className="space-y-1.5">
      {part.options.map((option, n) => {
        const status = graded ? graded.options.find((o) => o.option === option).status : ''
        const isPicked = picked.has(option)
        return (
          <button
            key={option}
            type="button"
            disabled={checked}
            onClick={() => onToggle(option)}
            aria-pressed={isPicked}
            style={{ '--i': n }}
            className={`rise-in option w-full flex items-center gap-3 px-3 py-2 rounded-[var(--radius-sm)] border text-left
              ${checked ? STATUS_CLASS[status] : isPicked ? 'border-[var(--primary)]' : 'border-[var(--border)]'}`}
          >
            <span
              aria-hidden="true"
              className="w-4 h-4 rounded shrink-0 border border-[var(--border-hi)]"
              style={isPicked ? { background: 'var(--primary)', borderColor: 'var(--primary)' } : undefined}
            />
            <span className="flex-1 flex items-center gap-3 text-left"><OptionText part={part} option={option} /></span>
            {checked && status && (
              <span className="type-small flex items-center gap-1.5">
                {(status === 'bad' || status === 'miss') && <RedDot />}
                {MARK_LABEL[status]}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
