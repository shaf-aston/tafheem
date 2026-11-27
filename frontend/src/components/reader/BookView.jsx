/**
 * One open book: the page, and back and on through it.
 *
 * The page is drawn as wide as the column it sits in and redrawn when that
 * changes. The arrow keys turn pages too, unless the reader is typing.
 */
import { useEffect, useRef, useState } from 'react'

import Stepper from '../ui/inputs/Stepper'

export default function BookView({ book, name }) {
  const [page, setPage] = useState(1)
  const [failed, setFailed] = useState(false)
  const frame = useRef(null)
  const canvas = useRef(null)
  const back = page > 1 ? () => setPage(page - 1) : null
  const on = page < book.pages ? () => setPage(page + 1) : null

  useEffect(() => {
    const draw = () => book.draw(page, canvas.current, frame.current.clientWidth).then(() => setFailed(false), () => setFailed(true))
    draw()
    const resized = new ResizeObserver(draw)
    resized.observe(frame.current)
    return () => resized.disconnect()
  }, [book, page])

  useEffect(() => {
    const key = (event) => {
      if (event.target.closest('input, textarea, [contenteditable]')) return
      if (event.key === 'ArrowLeft' && back) back()
      if (event.key === 'ArrowRight' && on) on()
    }
    addEventListener('keydown', key)
    return () => removeEventListener('keydown', key)
  })

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="type-body text-[var(--text-dim)] truncate">{name}</p>
        <div className="flex items-center gap-3 shrink-0">
          <span className="type-ui text-[var(--text-faint)]" aria-live="polite">Page {page} of {book.pages}</span>
          <Stepper label="page" onPrev={back} onNext={on} />
        </div>
      </div>
      <div ref={frame} className="rounded-[var(--radius-md)] overflow-hidden border border-[var(--border)]">
        <canvas ref={canvas} className="block" aria-label={`Page ${page} of ${name}`} />
      </div>
      {failed && <p className="type-body text-[var(--text-dim)]">This page could not be drawn.</p>}
    </div>
  )
}
