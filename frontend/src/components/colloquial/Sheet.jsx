// The focused view of one phrase: big picture, its words, the reply, and prev/next.
import { useEffect, useRef } from 'react'

import ArabicText from '../ui/ArabicText'
import SmallButton from '../ui/SmallButton'
import Face, { FOCUS } from './Face'
import OtherDialects from './OtherDialects'
import Spelling from './Spelling'

const FOCUSABLE = 'button, [href], [tabindex]:not([tabindex="-1"])'

export default function Sheet({ phrases, at, onAt, onClose, place }) {
  const box = useRef(null)
  const closeRef = useRef(null)
  const phrase = phrases[at]

  useEffect(() => {
    const opener = document.activeElement
    closeRef.current?.focus()
    const { overflow } = document.body.style
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = overflow
      opener?.focus?.()
    }
  }, [])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowRight' && at < phrases.length - 1) onAt(at + 1)
      else if (e.key === 'ArrowLeft' && at > 0) onAt(at - 1)
      else if (e.key === 'Tab') {
        const items = [...box.current.querySelectorAll(FOCUSABLE)].filter((el) => !el.disabled)
        const first = items[0]
        const last = items[items.length - 1]
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [at, phrases.length, onAt, onClose])

  return (
    <div
      className="fixed inset-0 z-[var(--layer-overlay)] flex items-end sm:items-center justify-center"
      style={{ background: 'color-mix(in srgb, var(--bg) 82%, transparent)' }}
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={box}
        role="dialog"
        aria-modal="true"
        aria-label={phrase.english}
        className="w-full sm:max-w-lg max-h-[100dvh] overflow-y-auto bg-[var(--surface)] border border-[var(--border-hi)]
          rounded-t-[var(--radius-md)] sm:rounded-[var(--radius-md)] shadow-[var(--shadow-pop)]"
      >
        <div className="relative">
          <Face
            key={at}
            phrase={phrase}
            index={at}
            arabicSize="lg"
            showEnglish={false}
            className="aspect-[4/3] w-full"
          />
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Close"
            className={`press absolute top-2 end-2 w-9 h-9 grid place-items-center rounded-full border border-[var(--border-hi)]
              bg-[var(--bg)] text-[var(--text)] ${FOCUS}`}
          >
            <span aria-hidden="true">✕</span>
          </button>
        </div>

        <div className="p-5 space-y-5">
          <div className="space-y-1 text-center">
            <Spelling size="body" className="block">{phrase.transliteration}</Spelling>
            <p className="type-ui font-semibold text-[var(--text)]">{phrase.english}</p>
          </div>

          {phrase.reply && (
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] px-4 py-3 text-center space-y-1">
              <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">They answer</p>
              <ArabicText as="p" size="base" className="text-[var(--text)]">{phrase.reply.arabic}</ArabicText>
              <Spelling className="block">{phrase.reply.transliteration}</Spelling>
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
    </div>
  )
}
