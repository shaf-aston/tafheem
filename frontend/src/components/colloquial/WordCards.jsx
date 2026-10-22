// Flash cards: the English first, a tap turns it to the Arabic; swipe or prev/next for the next word.
import { useState } from 'react'

import { isRight } from '../../lib/colloquialAnswer'
import { useSlide, useSwipe } from '../../lib/useSwipe'
import ArabicText from '../ui/ArabicText'
import MicButton from '../ui/MicButton'
import SmallButton from '../ui/SmallButton'
import SpeakButton from '../ui/SpeakButton'
import { FOCUS } from './Face'
import PhrasePicture from './PhrasePicture'
import Spelling from './Spelling'

export default function WordCards({ words }) {
  const [at, setAt] = useState(0)
  const [turned, setTurned] = useState(false)
  // What the microphone heard for this card, and whether it was the word.
  const [said, setSaid] = useState(null)
  const step = (to) => { setAt(to); setTurned(false); setSaid(null) }
  const swipe = useSwipe(at > 0 && (() => step(at - 1)), at < words.length - 1 && (() => step(at + 1)))
  const slide = useSlide(at)
  const word = words[at]

  // Clipped sideways so a dragged card never scrolls the page; the inset keeps focus rings whole.
  return (
    <div className="space-y-4 overflow-x-hidden -mx-1 px-1" {...swipe}>
      <div key={at} {...slide} className={`space-y-4 ${slide.className}`}>
        <button
          type="button"
          onClick={() => setTurned(!turned)}
          aria-label={turned ? `${word.arabic}, show the English` : `${word.english}, show the Arabic`}
          className={`press w-full min-h-48 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)]
            hover:border-[var(--border-hi)] flex flex-col items-center justify-center gap-2 p-6 ${FOCUS}`}
        >
          {/* The picture is the meaning without English, so it stays on both sides. */}
          {word.image && <PhrasePicture phrase={word} alt="" className="w-32 h-32 rounded-[var(--radius-md)]" />}
          {word.category && <span className="eyebrow">{word.category}</span>}
          {/* Keyed by side, so turning the card fades the other side in rather than snapping. */}
          <span key={String(turned)} className="fade-in flex flex-col items-center gap-2">
            {turned
              ? <ArabicText as="span" size="lg" className="text-[var(--text)]">{word.arabic}</ArabicText>
              : <span className="type-figure font-semibold text-[var(--text)]">{word.english}</span>}
            {/* The gloss under the Arabic is read, not a label, so it takes the reading size. */}
            <span className={turned ? 'type-body text-[var(--text-dim)]' : 'type-ui text-[var(--text-faint)]'}>{turned ? word.english : 'Tap to see the Arabic'}</span>
          </span>
        </button>
        <div className="flex items-center justify-center gap-2 min-h-8">
          {turned && <Spelling size="body">{word.transliteration}</Spelling>}
          <SpeakButton key={word.arabic} early text={word.arabic} />
          <MicButton anyArabic title="Say it" key={`mic-${at}`}
            onHeard={(heard) => { setSaid({ text: heard.text, right: isRight(heard.text, word.arabic.split(' / ')) }); setTurned(true) }} />
        </div>
        {/* Said aloud, then marked by the same rule as a typed answer: the
            vowel marks and a missing hamza are not mistakes. */}
        {said && (
          <p role="status" className="text-center type-small" style={{ color: said.right ? 'var(--success)' : 'var(--warn)' }}>
            {said.right ? 'Yes, that is it.' : 'Heard '}
            {!said.right && <ArabicText as="span" size="sm">{said.text}</ArabicText>}
            {!said.right && ', listen and try again.'}
          </p>
        )}
      </div>
      <div className="flex items-center justify-between gap-3">
        <SmallButton onClick={() => step(at - 1)} disabled={at === 0} aria-label="Previous word">← Prev</SmallButton>
        <span className="type-ui tabular-nums text-[var(--text-dim)]">{at + 1} / {words.length}</span>
        <SmallButton onClick={() => step(at + 1)} disabled={at === words.length - 1} aria-label="Next word">Next →</SmallButton>
      </div>
    </div>
  )
}
