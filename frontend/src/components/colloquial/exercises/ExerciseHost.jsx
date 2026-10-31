/**
 * One exercise, whatever its type: the prompt, the renderer for its type, the
 * Check button (none for a pick, which is marked as it is made) and what
 * follows it. The only reader of exercises/registry,
 * so nothing else knows how a type is drawn or marked.
 *
 * `onDone(correct, value)` lets a caller move on and keep the answer; `saved`
 * ({correct, value}) puts an answered exercise back as it was left, so coming
 * back to one shows what was written and how it was marked. The attempt itself
 * is filed here under module "colloq", so every place that hosts an exercise
 * records it alike; an exercise naming its own `progress` ({module, item}) is
 * filed there instead, as a word drill is filed under the word. An exercise with `say` is heard: its prompt gets a speaker.
 */
import { useEffect, useRef, useState } from 'react'

import { hasAnswer } from '../../../lib/colloquial/answer'
import { useRecord } from '../../../lib/learner/record'
import ArabicText from '../../ui/ArabicText'
import PrimaryButton from '../../ui/PrimaryButton'
import SpeakButton from '../../ui/SpeakButton'
import PhrasePicture from '../parts/PhrasePicture'
import { exerciseOf } from './registry'

const statusOf = (saved) => (!saved ? '' : saved.correct ? 'right' : 'wrong')

// Each Arabic run in an English prompt in its own <bdi>, so the quotes and the
// question mark around it stay where they were written.
const ARABIC_RUN = /([\u0600-\u06FF\u0750-\u077F](?:[\u0600-\u06FF\u0750-\u077F\s]*[\u0600-\u06FF\u0750-\u077F])?)/
function Isolated({ text }) {
  return String(text ?? '').split(ARABIC_RUN).map((part, i) => (i % 2 ? <bdi key={i} lang="ar">{part}</bdi> : part))
}

export default function ExerciseHost({ exercise, accent, saved, onDone }) {
  const { file } = useRecord()
  const kind = exerciseOf(exercise.type)
  const [value, setValue] = useState(() => saved?.value ?? kind?.blank ?? '')
  const [status, setStatus] = useState(() => statusOf(saved))
  // A heard question whose sound would not play: its spelling is shown instead.
  const [mute, setMute] = useState(false)
  // A typed or built answer gets a second go before the answer is shown; a pick shows it at once.
  const [again, setAgain] = useState(false)
  const startedAt = useRef(null)
  // A kind marked as it is picked has no first keystroke to start the clock, so it starts on sight.
  useEffect(() => { if (kind?.instant) startedAt.current = Date.now() }, [kind])

  if (!kind) {
    return (
      <p className="type-small text-[var(--warn)]">
        This lesson has a kind of exercise ({exercise.type}) this version cannot show yet.
      </p>
    )
  }

  const check = (given = value) => {
    const correct = kind.judge(exercise, given)
    if (!correct && !kind.instant && !again) return setAgain(true)
    setStatus(correct ? 'right' : 'wrong')
    const { module = 'colloq', item = exercise.id } = exercise.progress ?? {}
    file({ module, item, correct, ms: startedAt.current && Date.now() - startedAt.current })
    onDone?.(correct, given)
  }
  const change = (next) => {
    startedAt.current ??= Date.now()
    setValue(next)
    if (kind.instant) check(next)
  }

  // A correct-but-bookish answer is a note, never a mark against the learner.
  const bookish = exercise.too_formal
  const wasBookish = bookish && status && kind.judge({ ...exercise, accepted: [bookish.item] }, value)

  return (
    // Enter in the answer box checks it, as the Check button does.
    <div data-exercise className="space-y-4" onKeyDown={(e) => {
      if (e.key === 'Enter' && e.target.tagName === 'INPUT' && !status && !kind.instant && hasAnswer(value)) {
        e.preventDefault()
        check()
      }
    }}>
      {/* A picture question: the thing itself, to be named in Arabic. */}
      {exercise.image && <PhrasePicture phrase={{ image: exercise.image }} alt="The picture to name"
        className="w-40 h-40 mx-auto block rounded-[var(--radius-md)]" />}
      <p className="type-body text-[var(--text)] flex items-center gap-3">
        {exercise.say && <SpeakButton text={exercise.say} early onFail={() => setMute(true)} />}
        <span><Isolated text={exercise.prompt} /></span>
      </p>
      {mute && exercise.spelling && (
        <p role="status" className="type-small text-[var(--text-dim)]">
          No sound here. Read it instead: <span className="font-medium text-[var(--text)]">{exercise.spelling}</span>
        </p>
      )}
      <kind.Renderer exercise={exercise} value={value} onChange={change} status={status} accent={accent} />
      {!status && !kind.instant && (
        // check() with nothing: a bare onClick={check} would mark the click event itself as the answer.
        <PrimaryButton accent={accent} disabled={!hasAnswer(value)} onClick={() => check()}>
          Check
        </PrimaryButton>
      )}
      {wasBookish && (
        <p className="type-small text-[var(--text-dim)]">
          {/* "Is correct" only of what the learner gave; a right pick hears of the other form as an aside. */}
          {value === bookish.item ? <><ArabicText as="span" size="sm">{bookish.item}</ArabicText> is correct, but {bookish.feedback}</>
            : <>You may also hear <ArabicText as="span" size="sm">{bookish.item}</ArabicText>: {bookish.feedback}</>}
        </p>
      )}
      {/* The verdict, said aloud as it comes. A pick already marks its own option, so there it is only heard. */}
      <p role="status" className={kind.instant ? 'sr-only' : `type-small font-medium ${status === 'right' ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
        {status === 'right' ? '✓ Correct.' : status === 'wrong' ? '✗ Not quite.' : again ? 'Not quite: have one more go.' : ''}
      </p>
      {status && exercise.tip && <p className="type-small text-[var(--text-dim)]">{exercise.tip}</p>}
    </div>
  )
}
