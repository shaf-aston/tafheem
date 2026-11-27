/**
 * A tapped word, answered in place: what it means, what it is, what case it takes
 * and why. Drawn in the chart's side panel, or under the word's own line on a phone,
 * so it never covers the chart. The full card and the dictionary are one tap further.
 */
import { caseGloss, caseLabel, roleGloss } from '../../lib/nahw/grammarTerms'
import Gloss from '../grammar/Gloss'
import { roleVar } from '../../lib/nahw/roleColors'
import ArabicText from '../ui/text/ArabicText'
import CloseButton from '../ui/buttons/CloseButton'

// "… القاعدة: …" restates the reason as a rule, shown on a line of its own
const split = (reason) => {
  const [why, rule] = (reason ?? '').split('. القاعدة')
  return { why, rule: rule?.replace(/^[:：]\s*/, '') }
}

export default function WordDetail({ word, english, onClose, onMore, onLookup }) {
  const { why, rule } = split(word.reason)
  return (
    <div className="rise-in space-y-2 rounded-[var(--radius-md)] bg-[var(--surface-hi)] border border-[var(--border-hi)] p-3"
      style={{ borderInlineStartWidth: 3, borderInlineStartColor: roleVar(word.role_key) }}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <ArabicText className="text-[var(--text)] leading-tight">{word.word}</ArabicText>
          {english && <p className="type-small text-[var(--text-dim)]" lang="en">{english}</p>}
        </div>
        <CloseButton onClick={onClose} />
      </div>
      <p className="type-ui" dir="rtl" lang="ar">
        <span className="font-semibold" style={{ color: roleVar(word.role_key) }}>{word.name ?? word.role}</span>
        {word.case && <span className="text-[var(--text-dim)]"> · {caseLabel(word.case)}{word.sign ? ` (${word.sign})` : ''}</span>}
      </p>
      <Gloss>{[roleGloss(word.name) || roleGloss(word.role), caseGloss(word.case)].filter(Boolean).join(' · ')}</Gloss>
      {why && <p className="type-small text-[var(--text)] leading-relaxed" dir="rtl" lang="ar">{why}</p>}
      {rule && <p className="type-label text-[var(--text-dim)] leading-relaxed" dir="rtl" lang="ar">القاعدة: {rule}</p>}
      <div className="flex gap-3 pt-1 type-label">
        <button type="button" className="underline text-[var(--text-dim)] hover:text-[var(--text)]" onClick={onMore}>Full card</button>
        <button type="button" className="underline text-[var(--text-dim)] hover:text-[var(--text)]" onClick={onLookup}>Dictionary</button>
      </div>
    </div>
  )
}

WordDetail.Empty = function Empty() {
  return (
    <div className="h-full grid place-content-center text-center gap-1 text-[var(--text-faint)]">
      <span aria-hidden="true" className="text-2xl">☝</span>
      <p className="type-small">Tap any word in the chart<br />to see its role, case and why.</p>
    </div>
  )
}
