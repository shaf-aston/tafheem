// Question and answer as a matched pair of cards: press the question to turn it over.
import { useState } from 'react'

import ArabicText from '../ui/ArabicText'
import Pronunciation from '../ui/Pronunciation'
import { FOCUS } from './Face'

const FACE = `col-start-1 row-start-1 flex flex-col items-center justify-center gap-1 px-4 py-6 text-center
  rounded-[var(--radius-md)] border transition-[transform,opacity] [backface-visibility:hidden]`
const TURN = { transitionDuration: 'calc(var(--motion-base-ms) * 1ms)' }

function Side({ item, label, flipped, hidden, back }) {
  return (
    <span
      aria-hidden={hidden}
      style={{ ...TURN, transform: `rotateY(${flipped !== back ? 180 : 0}deg)` }}
      className={`${FACE} ${back ? 'border-[var(--border-hi)] bg-[var(--surface-hi)]' : 'border-[var(--border)] bg-[var(--surface)]'}`}
    >
      <span className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">{label}</span>
      <ArabicText as="span" size="base" className="block text-[var(--text)]">{item.arabic}</ArabicText>
      <Pronunciation>{item.transliteration}</Pronunciation>
      <span className="type-small text-[var(--text)]">{item.english}</span>
    </span>
  )
}

function PairCard({ pair, response }) {
  const [flipped, setFlipped] = useState(false)
  return (
    <button
      type="button"
      onClick={() => setFlipped(!flipped)}
      aria-pressed={flipped}
      aria-label={`${pair.english}. ${flipped ? 'Showing the answer' : 'Press to see the answer'}`}
      style={{ perspective: '900px' }}
      className={`press grid w-full rounded-[var(--radius-md)] ${FOCUS}`}
    >
      <Side item={pair} label="Ask" flipped={flipped} hidden={flipped} back={false} />
      <Side item={response} label="Answer" flipped={flipped} hidden={!flipped} back />
    </button>
  )
}

export default function Pairs({ pairs }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {pairs.map((p, i) => (
        <li key={i}><PairCard pair={p.pair} response={p.response} /></li>
      ))}
    </ul>
  )
}
