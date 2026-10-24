/**
 * A word tapped in the chart, answered where it was tapped: what it means, what it
 * is, what case it takes and why, in four short lines. The full card and the
 * dictionary are one tap further, so the tap never leaves the chart.
 *
 * Shuts on Escape or a press outside it.
 */
import { useEffect, useRef } from 'react'

import { caseLabel } from '../../lib/nahw/grammarTerms'
import { roleVar } from '../../lib/nahw/roleColors'
import ArabicText from '../ui/ArabicText'
import CloseButton from '../ui/CloseButton'

// "… القاعدة: …" restates the reason as a rule; the popup keeps the reason itself.
const reasonOnly = (reason) => (reason ?? '').split('. القاعدة')[0]

export default function WordPeek({ word, english, at, onClose, onMore, onLookup }) {
  const box = useRef(null)
  useEffect(() => {
    const outside = (event) => { if (!box.current?.contains(event.target)) onClose() }
    const escape = (event) => { if (event.key === 'Escape') onClose() }
    document.addEventListener('pointerdown', outside)
    document.addEventListener('keydown', escape)
    box.current?.focus()
    return () => {
      document.removeEventListener('pointerdown', outside)
      document.removeEventListener('keydown', escape)
    }
  }, [onClose])

  return (
    <div
      ref={box}
      role="dialog"
      aria-label={`${word.word}: ${word.role ?? ''}`}
      tabIndex={-1}
      className="rise-in absolute z-[var(--layer-tip)] w-[min(18rem,calc(100vw-2rem))] -translate-x-1/2 p-3 space-y-1.5
        rounded-[var(--radius-md)] bg-[var(--surface-hi)] border border-[var(--border-hi)] shadow-xl outline-none"
      style={{ left: at.x, top: at.y }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <ArabicText className="text-[var(--text)] leading-tight">{word.word}</ArabicText>
          {english && <p className="type-small text-[var(--text-dim)]" lang="en">{english}</p>}
        </div>
        <CloseButton onClick={onClose} />
      </div>
      <p className="text-sm" dir="rtl" lang="ar">
        <span style={{ color: roleVar(word.role_key) }}>{word.name ?? word.role}</span>
        {word.case && <span className="text-[var(--text-dim)]"> · {caseLabel(word.case)}{word.sign ? ` (${word.sign})` : ''}</span>}
      </p>
      {word.reason && <p className="text-xs text-[var(--text-dim)] leading-relaxed" dir="rtl" lang="ar">{reasonOnly(word.reason)}</p>}
      <div className="flex gap-3 pt-1 text-xs">
        <button type="button" className="underline text-[var(--text-dim)] hover:text-[var(--text)]" onClick={onMore}>Full card</button>
        <button type="button" className="underline text-[var(--text-dim)] hover:text-[var(--text)]" onClick={onLookup}>Dictionary</button>
      </div>
    </div>
  )
}
