/**
 * An example's written answers (the teacher's explanation, a translation),
 * and any doubt a reviewer has about the marking. Shared so Practise (after checking) and Browse (after Show
 * answer) print the same note the same way.
 */
import { doubtsOf, proseParts } from '../lib/tamreen'

const BY_LABEL = { teacher: 'Teacher', claude: 'AI-written' }

export default function TamreenAnswerNote({ example }) {
  const written = proseParts(example)
  const doubts = doubtsOf(example)
  if (written.length === 0 && doubts.length === 0) return null

  return (
    <div className="fade-in space-y-2">
      {written.map((part) => (
        <p key={part.letter} className="type-small text-[var(--text-dim)] border-l-2 border-[var(--border-hi)] pl-3">
          <span
            className="type-small mr-2 px-2 py-0.5 rounded-full border"
            style={{ color: 'var(--success)', borderColor: 'color-mix(in srgb, var(--success) 40%, transparent)' }}
          >
            {BY_LABEL[part.by] ?? part.by}
          </span>
          {part.answer}
        </p>
      ))}
      {doubts.map((doubt, i) => (
        <p
          key={i}
          role="note"
          className="type-small rounded-[var(--radius-sm)] border px-3 py-2"
          style={{
            borderColor: 'color-mix(in srgb, var(--warn) 40%, transparent)',
            background: 'color-mix(in srgb, var(--warn) 10%, transparent)',
            color: 'var(--text-dim)',
          }}
        >
          <strong style={{ color: 'var(--warn)' }}>A reviewer doubts the teacher&apos;s answer here.</strong> {doubt}
        </p>
      ))}
    </div>
  )
}
