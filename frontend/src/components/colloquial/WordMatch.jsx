// Match pairs: the English down one side, the Arabic down the other, mixed up. Tap
// one then its partner; a pair found fades, a wrong pair shakes. At most five at a
// time, split evenly, so a long topic is several short boards and none is tiny.
// A warm-up: nothing here is filed for review, since finding a word among five is
// easier than recalling it.
import { useState } from 'react'

import settings from '../../colloquial.json'
import { shuffled } from '../../lib/shuffle'
import ArabicText from '../ui/ArabicText'
import SmallButton from '../ui/SmallButton'
import { FOCUS } from './Face'

const BOARD = settings['match-board']
const SHAKE_MS = 360

const boardOf = (words, round) => {
  const size = Math.ceil(words.length / Math.ceil(words.length / BOARD))
  const these = words.slice(round * size, round * size + size)
  return { round, left: shuffled(these, Math.random), right: shuffled(these, Math.random), found: [], slips: 0 }
}

export default function WordMatch({ words }) {
  const rounds = Math.ceil(words.length / BOARD)
  const [board, setBoard] = useState(() => boardOf(words, 0))
  const [picked, setPicked] = useState(null)   // { side, arabic }
  const [missed, setMissed] = useState([])     // the two tiles shaking, as `${side}:${arabic}`
  const done = board.found.length === board.left.length

  const tap = (side, arabic) => {
    if (board.found.includes(arabic)) return
    if (!picked || picked.side === side) return setPicked({ side, arabic })
    setPicked(null)
    if (picked.arabic === arabic) return setBoard((b) => ({ ...b, found: [...b.found, arabic] }))
    setBoard((b) => ({ ...b, slips: b.slips + 1 }))
    setMissed([`${picked.side}:${picked.arabic}`, `${side}:${arabic}`])
    setTimeout(() => setMissed([]), SHAKE_MS)
  }
  const restart = (round) => { setPicked(null); setBoard(boardOf(words, round)) }

  const tile = (side, word) => {
    const id = `${side}:${word.arabic}`
    const found = board.found.includes(word.arabic)
    const on = picked?.side === side && picked.arabic === word.arabic
    return (
      <li key={id}>
        <button
          type="button"
          disabled={found}
          aria-pressed={on}
          onClick={() => tap(side, word.arabic)}
          className={`press w-full min-h-14 rounded-[var(--radius)] border-2 bg-[var(--surface)] px-3 py-2 transition-[opacity,border-color] ${FOCUS}
            ${found ? 'opacity-30 border-[var(--success)]' : on ? 'border-[var(--primary)]' : 'border-[var(--border)] hover:border-[var(--border-hi)]'}
            ${missed.includes(id) ? 'shake border-[var(--danger)]' : ''}`}
        >
          {side === 'en'
            ? <span className="type-body font-medium text-[var(--text)]">{word.english}</span>
            : <ArabicText as="span" size="base" className="text-[var(--text)]">{word.arabic}</ArabicText>}
        </button>
      </li>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <ul className="space-y-2" aria-label="English">{board.left.map((w) => tile('en', w))}</ul>
        <ul className="space-y-2" aria-label="Arabic">{board.right.map((w) => tile('ar', w))}</ul>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="type-small text-[var(--text-dim)]" aria-live="polite">
          {done ? 'All matched' : `${board.found.length} of ${board.left.length} matched`} · {board.slips} {board.slips === 1 ? 'slip' : 'slips'}
          {rounds > 1 && ` · board ${board.round + 1} of ${rounds}`}
        </span>
        {done && (board.round < rounds - 1
          ? <SmallButton onClick={() => restart(board.round + 1)}>Next board →</SmallButton>
          : <SmallButton onClick={() => restart(0)}>Play again</SmallButton>)}
      </div>
    </div>
  )
}
