// The questions beside the answer; a search spanning topics names each one's topic.
export default function QuestionList({ rows, current, accent, onPick }) {
  return (
    <ol className="space-y-1">
      {rows.map(({ topic, question }, i) => {
        const on = question.id === current
        return (
          <li key={question.id} className="rise-in" style={{ '--i': i }}>
            <button
              type="button"
              onClick={() => onPick(question.id)}
              aria-current={on ? 'true' : undefined}
              style={on ? { borderColor: accent, color: 'var(--text)' } : undefined}
              className="press w-full text-left rounded-[var(--radius-sm)] border-s-2 border-transparent
                px-3 py-2 text-sm text-[var(--text-dim)] hover:text-[var(--text)] hover:bg-[var(--surface-hi)]
                transition-colors"
            >
              {question.q}
              {rows.some((r) => r.topic !== topic) && (
                <span className="block type-tiny text-[var(--text-faint)] mt-0.5">{topic.title}</span>
              )}
            </button>
          </li>
        )
      })}
    </ol>
  )
}
