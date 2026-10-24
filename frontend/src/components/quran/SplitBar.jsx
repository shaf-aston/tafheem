import { useRef } from 'react'

import QURAN from '../../config/quran.json'

const { split: SPLIT } = QURAN
const { least: LEAST, full: FULL } = SPLIT
const clampShare = (n) => Math.min(1 - LEAST, Math.max(FULL, n))
// How far a press may move and still be a tap on the sheet's handle, in px.
const TAP_SLOP = 6

/**
 * The sheet's handle on a phone: drag it, press the arrows on it, or tap it,
 * to give the surah or the study more room. A tap swaps between the sheet
 * opening size and the whole screen, and a drag that ends near the top snaps
 * to the whole screen so no sliver of surah is left.
 */
export default function SplitBar({ panes, share, onShare }) {
  const from = useRef(null)
  const drag = (e) => {
    if (!e.currentTarget.hasPointerCapture(e.pointerId)) return
    const box = panes.current.getBoundingClientRect()
    onShare(clampShare((e.clientY - box.top) / box.height))
  }
  const release = (e) => {
    if (Math.abs(e.clientY - from.current) < TAP_SLOP) onShare(share > FULL ? FULL : SPLIT.share)
    else if (share < SPLIT.step) onShare(FULL)
  }
  const step = { ArrowUp: -SPLIT.step, ArrowDown: SPLIT.step }
  return (
    <div
      role="separator"
      aria-orientation="horizontal"
      aria-label="Resize the surah and the study"
      aria-valuenow={Math.round(share * 100)}
      aria-valuemin={FULL * 100}
      aria-valuemax={(1 - LEAST) * 100}
      tabIndex={0}
      onPointerDown={(e) => { from.current = e.clientY; e.currentTarget.setPointerCapture(e.pointerId) }}
      onPointerMove={drag}
      onPointerUp={release}
      onKeyDown={(e) => step[e.key] && (e.preventDefault(), onShare(clampShare(share + step[e.key])))}
      className="touch-none select-none shrink-0 grid place-items-center h-8 cursor-row-resize rounded-t-[var(--radius-lg)]
        border-t border-[var(--border-hi)] bg-[var(--surface)] shadow-[var(--shadow-pop)] focus:outline-none focus-visible:bg-[var(--surface-hi)]"
    >
      <span aria-hidden="true" className="w-10 h-1 rounded-full bg-[var(--border-hi)]" />
    </div>
  )
}
