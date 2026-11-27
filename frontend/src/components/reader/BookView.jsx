/**
 * One open book: the page, and back and on through it.
 *
 * Shown whole by default, so a page is read without scrolling; "Fit width"
 * draws it as wide as the column for small print. Pages turn by the arrows,
 * the arrow keys (unless typing), a sideways swipe, or typing a page number.
 * A turn in fit-width brings the new page's top into view.
 */
import { useEffect, useRef, useState } from 'react'

import knobs from '../../config/reader.json'
import { useRemembered } from '../../lib/store/useRemembered'

import Stepper from '../ui/inputs/Stepper'
import Segmented from '../ui/inputs/Segmented'

/** The screen's height between the app's own bars, top and bottom, in px. */
function between() {
  const top = document.querySelector('header')?.getBoundingClientRect().bottom ?? 0
  const bars = [...document.querySelectorAll('nav')].map((n) => n.getBoundingClientRect()).filter((r) => r.height && r.bottom >= innerHeight - 1)
  return { top: Math.max(top, 0), bottom: Math.min(innerHeight, ...bars.map((r) => r.top)) }
}

const FITS = [{ id: 'page', label: 'Whole page' }, { id: 'width', label: 'Fit width' }]

export default function BookView({ book, name, start = 1, accent, onPage }) {
  const [page, setPage] = useState(Math.min(start, book.pages))
  const [failed, setFailed] = useState(false)
  const [width, setWidth] = useState(0)
  const [fit, setFit] = useRemembered('reader.fit', FITS.map((f) => f.id))
  const frame = useRef(null)
  const canvas = useRef(null)
  const swipe = useRef(null)
  const controls = useRef(null)
  const go = (n) => setPage(Math.min(Math.max(n, 1), book.pages))
  const back = page > 1 ? () => go(page - 1) : null
  const on = page < book.pages ? () => go(page + 1) : null

  // Redrawn when the column's width changes, not its height: drawing a page sets the height.
  useEffect(() => {
    const resized = new ResizeObserver(([entry]) => setWidth(Math.round(entry.contentRect.width)))
    resized.observe(frame.current)
    return () => resized.disconnect()
  }, [])

  useEffect(() => {
    if (!width) return
    const { top, bottom } = between()
    const room = bottom - top - controls.current.offsetHeight - knobs['page-margin-px'] * 2
    const height = fit === 'page' ? Math.max(room, 200) : Infinity
    book.draw(page, canvas.current, width, height).then(() => setFailed(false), () => setFailed(true))
  }, [book, page, width, fit])

  useEffect(() => { onPage?.(page) }, [onPage, page])

  // A book opens with its controls just under the app's header, so a whole page shows at once.
  useEffect(() => {
    scrollTo({ top: scrollY + controls.current.getBoundingClientRect().top - between().top - knobs['page-margin-px'] })
  }, [])

  // A turn while reading down a tall page starts the next at its top.
  useEffect(() => {
    const top = controls.current.getBoundingClientRect().top - between().top
    if (top < 0) scrollTo({ top: scrollY + top - knobs['page-margin-px'] })
  }, [page])

  useEffect(() => {
    const key = (event) => {
      if (event.target.closest('input, textarea, [contenteditable]')) return
      const step = { ArrowLeft: -1, ArrowRight: 1 }[event.key]
      if (step) setPage((n) => Math.min(Math.max(n + step, 1), book.pages))
    }
    addEventListener('keydown', key)
    return () => removeEventListener('keydown', key)
  }, [book])

  const swiped = (event) => {
    const from = swipe.current
    swipe.current = null
    if (!from || event.pointerType === 'mouse') return
    const across = event.clientX - from.x
    if (Math.abs(across) > knobs['swipe-px'] && Math.abs(across) > Math.abs(event.clientY - from.y)) go(page + (across < 0 ? 1 : -1))
  }

  return (
    <div className="space-y-3">
      <div ref={controls} className="flex flex-wrap items-center justify-between gap-3">
        <p className="type-body text-[var(--text-dim)] truncate min-w-0">{name}</p>
        <div className="flex flex-wrap items-center gap-3">
          <Segmented label="How the page fits" accent={accent} value={fit} onChange={setFit} compact options={FITS} />
          <label className="flex items-center gap-1.5 type-ui text-[var(--text-faint)]">
            Page
            <input
              key={page}
              type="number"
              inputMode="numeric"
              min={1}
              max={book.pages}
              defaultValue={page}
              aria-label={`Page number, 1 to ${book.pages}`}
              onKeyDown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
              onBlur={(event) => { const n = Number(event.currentTarget.value); if (n) go(Math.round(n)) }}
              className="w-14 px-1.5 py-0.5 text-center rounded-[var(--radius-sm)] border border-[var(--border)] bg-transparent text-[var(--text)]"
            />
            <span aria-live="polite">of {book.pages}</span>
          </label>
          <Stepper label="page" onPrev={back} onNext={on} />
        </div>
      </div>
      <div ref={frame} className="flex justify-center">
        <canvas
          ref={canvas}
          className="block rounded-[var(--radius-md)] border border-[var(--border)] touch-pan-y"
          aria-label={`Page ${page} of ${name}`}
          onPointerDown={(event) => { swipe.current = { x: event.clientX, y: event.clientY } }}
          onPointerUp={swiped}
          onPointerCancel={() => { swipe.current = null }}
        />
      </div>
      {failed && <p className="type-body text-[var(--text-dim)]">This page could not be drawn.</p>}
    </div>
  )
}
