/**
 * One exercise, whatever its type: the prompt, the renderer for its type, the
 * Check button and what follows it. The only reader of exercises/registry,
 * so nothing else knows how a type is drawn or marked.
 *
 * `onDone(correct, value)` lets a caller move on and keep the answer; `saved`
 * ({correct, value}) puts an answered exercise back as it was left, so coming
 * back to one shows what was written and how it was marked. The attempt itself
 * is filed here under module "colloq", so every place that hosts an exercise
 * records it alike; an exercise naming its own `progress` ({module, item}) is
 * filed there instead, as a word drill is filed under the word. An exercise with `say` is heard: its prompt gets a speaker.
 */
import { useRef, useState } from 'react'

import { hasAnswer } from '../../lib/colloquialAnswer'
import { recordAttempt } from '../../lib/progress'
import ArabicText from '../ui/ArabicText'
import PrimaryButton from '../ui/PrimaryButton'
import SpeakButton from '../ui/SpeakButton'
import { exerciseOf } from './exercises/registry'

const statusOf = (saved) => (!saved ? '' : saved.correct ? 'right' : 'wrong')

export default function ExerciseHost({ exercise, accent, saved, onDone }) {
  const kind = exerciseOf(exercise.type)
  const [value, setValue] = useState(() => saved?.value ?? kind?.blank ?? '')
  const [status, setStatus] = useState(() => statusOf(saved))
  const startedAt = useRef(null)

  if (!kind) {
    return (
      <p className="type-small text-[var(--warn)]">
        This lesson has a kind of exercise ({exercise.type}) this version cannot show yet.
      </p>
    )
  }

  const check = () => {
    const correct = kind.judge(exercise, value)
    setStatus(correct ? 'right' : 'wrong')
    const { module = 'colloq', item = exercise.id } = exercise.progress ?? {}
    recordAttempt({ module, item, correct, ms: startedAt.current && Date.now() - startedAt.current })
    onDone?.(correct, value)
  }

  // A correct-but-bookish answer is a note, never a mark against the learner.
  const bookish = exercise.too_formal
  const wasBookish = bookish && status && kind.judge({ ...exercise, accepted: [bookish.item] }, value)

  return (
    <div className="space-y-4">
      <p className="type-body text-[var(--text)] flex items-center gap-3">
        {exercise.say && <SpeakButton text={exercise.say} early />}
        {exercise.prompt}
      </p>
      <kind.Renderer exercise={exercise} value={value} onChange={(next) => { startedAt.current ??= Date.now(); setValue(next) }} status={status} />
      {!status && (
        <PrimaryButton accent={accent} disabled={!hasAnswer(value)} onClick={check}>
          Check
        </PrimaryButton>
      )}
      {wasBookish && (
        <p className="type-small text-[var(--text-dim)]">
          <ArabicText as="span" size="sm">{bookish.item}</ArabicText> is correct, but {bookish.feedback}
        </p>
      )}
      {status && exercise.tip && <p className="type-small text-[var(--text-dim)]">{exercise.tip}</p>}
    </div>
  )
}
