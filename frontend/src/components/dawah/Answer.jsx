import CopyButton from '../ui/CopyButton'
import Chip from '../ui/Chip'
import Segmented from '../ui/Segmented'
import SourceBadge from '../ui/SourceBadge'
import { GoButton } from '../ui/RootActions'
import Argument from './Argument'

// One answer: the reply in short, the reasoning point by point, then further reading.
export default function Answer({ topic, question, library, accent, onGo, step, mode, modes, onMode, copy }) {
  const fatwa = question.islamqa
  return (
    <article key={question.id} className="fade-in rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-5">
      <div className="space-y-2">
        <p className="type-tiny uppercase tracking-wide" style={{ color: accent }}>{topic.title}</p>
        <h3 className="text-xl font-semibold leading-snug text-[var(--text)]">{question.q}</h3>
      </div>

      <div
        className="rounded-[var(--radius-sm)] p-4 flex gap-3 items-start justify-between"
        style={{ background: `color-mix(in srgb, ${accent} 10%, transparent)` }}
      >
        <div className="space-y-1">
          <p className="type-tiny uppercase tracking-wide text-[var(--text-faint)]">{copy.short}</p>
          <p className="text-[var(--text)] leading-relaxed">{question.short}</p>
        </div>
        <CopyButton text={question.short} label={copy.copy} />
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <p className="type-small font-medium text-[var(--text-dim)]">{copy.reasoning}</p>
          <Segmented label={copy['mode-label']} options={modes} value={mode} onChange={onMode} accent={accent} />
        </div>
        <Argument key={`${question.id}-${mode}`} points={question.points} library={library} accent={accent} mode={mode} copy={copy} onGo={onGo} />
      </div>

      <div className="flex items-center justify-between gap-2 flex-wrap pt-3 border-t border-[var(--border)]">
        {fatwa ? (
          <Chip cite accent={accent} href={library.islamqa.cite.replace('{number}', fatwa.number)} title={fatwa.title}>
            {copy['read-more']} {library.islamqa.name} {fatwa.number}
          </Chip>
        ) : <span />}
        <div className="flex gap-2">
          {step.prev && <GoButton onClick={step.prev}>{copy.previous}</GoButton>}
          {step.next && <GoButton onClick={step.next}>{copy['next-question']}</GoButton>}
        </div>
      </div>

      <SourceBadge source={library.source} />
    </article>
  )
}
