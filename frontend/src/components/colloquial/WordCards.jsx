// Flash cards: the English first, a tap turns it to the Arabic; swipe or prev/next for the next word.
import { useState } from 'react'

import { useSwipe } from '../../lib/useSwipe'
import ArabicText from '../ui/ArabicText'
import SmallButton from '../ui/SmallButton'
import SpeakButton from '../ui/SpeakButton'
import { FOCUS } from './Face'
import Spelling from './Spelling'

export default function WordCards({ words }) {
  const [at, setAt] = useState(0)
  const [turned, setTurned] = useState(false)
  const step = (to) => { setAt(to); setTurned(false) }
  const swipe = useSwipe(at > 0 && (() => step(at - 1)), at < words.length - 1 && (() => step(at + 1)))
  const word = words[at]

  return (
    <div className="space-y-4" {...swipe}>
      <button
        type="button"
        onClick={() => setTurned(!turned)}
        aria-label={turned ? `${word.arabic}, show the English` : `${word.english}, show the Arabic`}
        className={`press w-full min-h-48 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)]
          hover:border-[var(--border-hi)] flex flex-col items-center justify-center gap-2 p-6 ${FOCUS}`}
      >
        {word.category && <span className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">{word.category}</span>}
        {turned
          ? <ArabicText as="span" size="lg" className="text-[var(--text)]">{word.arabic}</ArabicText>
          : <span className="type-figure font-semibold text-[var(--text)]">{word.english}</span>}
        <span className="type-small text-[var(--text-faint)]">{turned ? word.english : 'Tap to see the Arabic'}</span>
      </button>
      <div className="flex items-center justify-center gap-2 min-h-8">
        {turned && <Spelling size="body">{word.transliteration}</Spelling>}
        <SpeakButton key={word.arabic} early text={word.arabic} />
      </div>
      <div className="flex items-center justify-between gap-3">
        <SmallButton onClick={() => step(at - 1)} disabled={at === 0} aria-label="Previous word">← Prev</SmallButton>
        <span className="type-small tabular-nums text-[var(--text-dim)]">{at + 1} / {words.length}</span>
        <SmallButton onClick={() => step(at + 1)} disabled={at === words.length - 1} aria-label="Next word">Next →</SmallButton>
      </div>
    </div>
  )
}
