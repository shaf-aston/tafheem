// The focused view of one phrase: big picture, its words, the reply, and prev/next (or a swipe).
import { useEffect } from 'react'

import { useSwipe } from '../../lib/useSwipe'

import ArabicText from '../ui/ArabicText'
import BottomSheet from '../ui/BottomSheet'
import CloseButton from '../ui/CloseButton'
import SmallButton from '../ui/SmallButton'
import SpeakButton from '../ui/SpeakButton'
import Face, { FOCUS } from './Face'
import OtherDialects from './OtherDialects'
import Spelling from './Spelling'

export default function Sheet({ phrases, at, onAt, onClose, place }) {
  const phrase = phrases[at]
  const swipe = useSwipe(at > 0 && (() => onAt(at - 1)), at < phrases.length - 1 && (() => onAt(at + 1)))

  // Arrows step through the phrases; Esc, focus and the backdrop are the sheet's.
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'ArrowRight' && at < phrases.length - 1) onAt(at + 1)
      else if (e.key === 'ArrowLeft' && at > 0) onAt(at - 1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [at, phrases.length, onAt])

  return (
    <BottomSheet label={phrase.english} onClose={onClose} className="max-h-[var(--sheet-tall)] overflow-y-auto">
      <div {...swipe}>
        <div className="relative">
          <Face
            key={at}
            phrase={phrase}
            index={at}
            arabicSize="lg"
            showEnglish={false}
            className="aspect-[2/1] w-full"
          />
          <CloseButton onClick={onClose} className={`absolute top-2 end-2 bg-[var(--bg)] ${FOCUS}`} />
        </div>

        <div className="p-5 space-y-5">
          <div className="space-y-1 text-center">
            <div className="flex flex-wrap items-center justify-center gap-x-2">
              <Spelling size="body">{phrase.transliteration}</Spelling>
              <SpeakButton key={phrase.arabic} early text={phrase.arabic} />
            </div>
            <p className="type-ui font-semibold text-[var(--text)]">{phrase.english}</p>
          </div>

          {phrase.reply && (
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] px-4 py-3 text-center space-y-1">
              <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">They answer</p>
              <ArabicText as="p" size="base" className="text-[var(--text)]">{phrase.reply.arabic}</ArabicText>
              <div className="flex flex-wrap items-center justify-center gap-x-2">
                <Spelling>{phrase.reply.transliteration}</Spelling>
                <SpeakButton key={phrase.reply.arabic} early text={phrase.reply.arabic} />
              </div>
              <p className="type-small text-[var(--text)]">{phrase.reply.english}</p>
            </div>
          )}

          <OtherDialects place={place} slot={phrase.slot} />

          <div className="flex items-center justify-between gap-3">
            <SmallButton onClick={() => onAt(at - 1)} disabled={at === 0} aria-label="Previous phrase">← Prev</SmallButton>
            <span className="type-small tabular-nums text-[var(--text-dim)]">{at + 1} / {phrases.length}</span>
            <SmallButton onClick={() => onAt(at + 1)} disabled={at === phrases.length - 1} aria-label="Next phrase">Next →</SmallButton>
          </div>
        </div>
      </div>
    </BottomSheet>
  )
}
