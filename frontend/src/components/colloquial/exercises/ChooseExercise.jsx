/**
 * Pick one of the offered answers.
 *
 * Text options are the Quiz tab's own numbered options (quiz/QuizOption), with
 * its 1-4 keys, so a pick looks, moves and answers the same in both places.
 * Picture options are a grid of tiles. Same exercise type either way, because
 * the learner is doing the same thing, and an option is told apart by carrying
 * an image or not. A picture that fails to load leaves its word, so a lesson
 * never breaks on one missing file.
 */
import { useState } from 'react'

import { colloquialImageUrl } from '../../../api'
import { useAnswerKeys } from '../../../lib/quiz/useAnswerKeys'
import { sayIn } from '../../../lib/text/say'
import QuizOption from '../../practice/QuizOption'
import ArabicText from '../../ui/text/ArabicText'

const say = sayIn('en')

const labelOf = (option) => (typeof option === 'string' ? option : option.label)

function Picture({ file, alt }) {
  const [gone, setGone] = useState(false)
  if (!file || gone) return null
  return (
    <img
      src={colloquialImageUrl(file)}
      alt={alt}
      loading="lazy"
      onError={() => setGone(true)}
      className="w-full aspect-[4/3] object-cover rounded-[var(--radius-sm)] bg-[var(--surface-hi)]"
    />
  )
}

export default function ChooseExercise({ exercise, value, onChange, status, accent }) {
  const answered = Boolean(status)
  const labels = exercise.options.map(labelOf)
  const pictures = exercise.options.some((option) => typeof option !== 'string')
  useAnswerKeys({ checked: answered, optionCount: labels.length }, {
    toggle: (e, index) => !answered && onChange(labels[index]),
  })

  if (!pictures) {
    return (
      <div className="grid sm:grid-cols-2 gap-2.5" role="group" aria-label="Answers">
        {labels.map((label, i) => (
          <QuizOption
            key={label}
            option={{ id: label, text: label }}
            index={i}
            lang="ar"
            say={say}
            answered={answered}
            picked={value}
            answerId={exercise.answer}
            accent={accent}
            onChoose={onChange}
          />
        ))}
      </div>
    )
  }

  return (
    <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {exercise.options.map((option) => {
        const label = labelOf(option)
        const mine = value === label
        // Once answered, the right one is always marked, and a wrong pick is
        // marked as well, so the learner sees both what they chose and what
        // was meant.
        const tone = !answered ? null
          : label === exercise.answer ? 'var(--success)'
          : mine ? 'var(--danger)' : null
        return (
          <li key={label}>
            <button
              type="button"
              disabled={answered}
              aria-pressed={mine}
              onClick={() => onChange(label)}
              style={{ borderColor: tone ?? (mine ? 'var(--border-hi)' : 'var(--border)') }}
              className={`w-full rounded-[var(--radius)] border bg-[var(--surface)] p-3 text-start
                transition-colors hover:border-[var(--border-hi)] disabled:hover:border-inherit
                ${answered && !tone ? 'opacity-55' : ''}`}
            >
              <Picture file={option.image} alt={label} />
              <ArabicText as="span" size="base" className="mt-2 block text-center">
                {label}
              </ArabicText>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
