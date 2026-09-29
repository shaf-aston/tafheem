/**
 * A hadith's grading, said quietly: a coloured dot and the leading verdict.
 * Press it for the next layer, every scholar's verdict and the hadith's page
 * on sunnah.com. Which verdict leads, and which colour it wears, is
 * lib/hadithGrade reading hadith.json; this file only draws.
 */
import { familyOf, leadGrade } from '../../lib/hadithGrade'

import Popover from './Popover'

const TONE = { success: 'var(--success)', warn: 'var(--warn)', danger: 'var(--danger)' }

function Dot({ grade }) {
  const tone = TONE[familyOf(grade)?.tone] ?? 'var(--text-faint)'
  return <span aria-hidden="true" style={{ background: tone }} className="inline-block w-1.5 h-1.5 rounded-full shrink-0" />
}

/** `sahihBy` names the Sahih collection a hadith comes from, which grades every hadith in it itself. */
export default function GradeMark({ grades = [], sahihBy = null, cite = '' }) {
  const lead = leadGrade(grades, sahihBy)
  if (!lead && !cite) return null
  const all = grades.length ? grades : lead ? [lead] : []

  return (
    <Popover
      label={lead ? <><Dot grade={lead.grade} />{lead.grade}</> : 'Source'}
      title={lead ? `Graded ${lead.grade} by ${lead.by}. Press for every grading.` : 'Where this hadith is checked'}
    >
      <div className="space-y-2 max-w-[min(18rem,80vw)]">
        {all.length > 0 && (
          <ul className="m-0 p-0 list-none space-y-1">
            {all.map((g) => (
              <li key={g.by} className="flex items-center gap-2 type-small">
                <Dot grade={g.grade} />
                <span className="text-[var(--text)]">{g.grade}</span>
                <span className="text-[var(--text-faint)]">{g.by}</span>
              </li>
            ))}
          </ul>
        )}
        {cite && (
          <a href={cite} target="_blank" rel="noreferrer" className="block type-small text-[var(--text-dim)] hover:text-[var(--text)] underline underline-offset-2">
            Read on sunnah.com &#8599;
          </a>
        )}
      </div>
    </Popover>
  )
}
