/**
 * Build the sentence from a bank of tiles.
 *
 * Tapping, not dragging: dragging is the thing that does not work on a phone,
 * and this is meant to be done on one. Tap a tile in the bank to add it to the
 * end of the sentence, tap it in the sentence to take it back.
 *
 * The bank is right to left like the sentence, so the first word of a Damascene
 * sentence is the first tile the eye lands on.
 */
import { useMemo } from 'react'

import { bankOf } from '../../../lib/colloquialAnswer'
import { shuffled } from '../../../lib/shuffle'
import ArabicText from '../../ui/ArabicText'

/**
 * The tiles in a fixed scrambled order for this exercise. Fixed, because a new
 * order on every keystroke would move the tiles under the learner's finger, and
 * it comes from the exercise's own id so the same exercise is the same puzzle
 * each time it is opened.
 */
const scramble = (exercise) => {
  let seed = [...exercise.id].reduce((total, letter) => total * 31 + letter.charCodeAt(0), 7) % 2147483647
  const next = () => (seed = (seed * 48271) % 2147483647) / 2147483647
  return shuffled(bankOf(exercise), next)
}

function Tile({ word, onClick, dim }) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        disabled={!onClick}
        className={`rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)]
          px-3 py-1.5 transition-colors hover:border-[var(--border-hi)] ${dim ? 'opacity-30' : ''}`}
      >
        <ArabicText as="span" size="sm">{word}</ArabicText>
      </button>
    </li>
  )
}

export default function ReorderExercise({ exercise, value, onChange, status }) {
  const bank = useMemo(() => scramble(exercise), [exercise])
  const chosen = value ?? []
  const answered = Boolean(status)
  // The value is the words themselves, so whatever holds it can read the
  // sentence without knowing this scrambled order. A sentence may use the same
  // word twice, so tiles are used up by count: the nth copy taken greys the nth
  // copy in the bank, and the other copies stay tappable.
  const taken = {}
  const used = bank.map((word) => {
    taken[word] = (taken[word] ?? 0) + 1
    return taken[word] <= chosen.filter((one) => one === word).length
  })

  return (
    <div className="space-y-3">
      <ol
        dir="rtl"
        style={{ borderColor: status === 'wrong' ? 'var(--danger)' : status === 'right' ? 'var(--success)' : 'var(--border)' }}
        className="flex min-h-[3.25rem] flex-wrap items-center gap-2 rounded-[var(--radius)] border
          border-dashed bg-[var(--surface)] p-2"
      >
        {chosen.length === 0 && (
          <li className="type-small px-2 text-[var(--text-faint)]" dir="ltr">Tap the words below, in order</li>
        )}
        {chosen.map((word, place) => (
          <Tile
            key={`${word}-${place}`}
            word={word}
            onClick={answered ? null : () => onChange(chosen.filter((_, i) => i !== place))}
          />
        ))}
      </ol>
      <ul dir="rtl" className="flex flex-wrap gap-2">
        {bank.map((word, at) => (
          <Tile
            key={at}
            word={word}
            dim={used[at]}
            onClick={answered || used[at] ? null : () => onChange([...chosen, word])}
          />
        ))}
      </ul>
      {status === 'wrong' && (
        <p className="type-small text-[var(--text-dim)]">
          In order it is <ArabicText size="sm">{exercise.answer}</ArabicText>
        </p>
      )}
    </div>
  )
}
