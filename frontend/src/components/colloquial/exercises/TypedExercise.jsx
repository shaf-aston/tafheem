/**
 * The three exercises answered by typing: reply, fill a gap, say it in Arabic.
 *
 * One box, right to left, in the Arabic face. The transliteration is accepted
 * too where one is listed, so the box is not forced into Arabic input: a learner
 * without an Arabic keyboard can still answer, and lib/colloquial/answer.js takes
 * either. The placeholder says which.
 */
import { takesLatin } from '../../../lib/colloquial/answer'
import ArabicText from '../../ui/ArabicText'

export default function TypedExercise({ exercise, value, onChange, status }) {
  const answered = Boolean(status)
  return (
    <div className="space-y-2">
      <label className="block">
        <span className="sr-only">Your answer</span>
        <ArabicText
          as="input"
          size="base"
          dir="auto"
          value={value}
          readOnly={answered}
          onChange={(event) => onChange(event.target.value)}
          // In English, which a beginner can read, and saying which letters will be marked.
          placeholder={takesLatin(exercise.accepted) ? 'Type it in Arabic, or how it sounds' : 'Type it in Arabic letters'}
          className={`w-full rounded-[var(--radius)] border bg-[var(--surface)] px-4 py-3
            outline-none transition-colors focus:border-[var(--border-hi)]
            ${answered ? 'opacity-70' : ''}`}
          style={{
            borderColor: status === 'wrong' ? 'var(--danger)' : status === 'right' ? 'var(--success)' : 'var(--border)',
            // The Arabic class sets right to left, over dir="auto": an answer in Latin letters
            // ("ismak eh?") and the English placeholder read left to right, or the question
            // mark lands at the front.
            direction: /[\u0600-\u06FF]/.test(value) ? 'rtl' : 'ltr',
          }}
        />
      </label>
      {status === 'wrong' && (
        // The right answer, once. Hiding it would leave the learner with a cross
        // and nothing to learn from.
        <p className="type-small text-[var(--text-dim)]">
          The natural answer is <ArabicText size="sm">{exercise.answer}</ArabicText>
        </p>
      )}
    </div>
  )
}
