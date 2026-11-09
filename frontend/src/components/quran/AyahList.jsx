import { useDeferredValue, useLayoutEffect } from 'react'

import { rowAt, showRow } from '../../lib/quran/surahRows'
import QURAN from '../../config/quran.json'

const { 'first-paint-rows': FIRST_PAINT_ROWS } = QURAN

// What the reader does to take over the scrolling from the page.
const TAKE_OVER = ['pointerdown', 'wheel', 'touchstart', 'keydown']

/**
 * The rows of one surah, in a pane that scrolls on its own. A new surah is a
 * new list (the reader keys it), so it starts with only the first screen of
 * rows drawn, the rest following once those are on screen. `target` is the
 * ayah to open at: it may be past the first screen, so it is scrolled to once
 * its row exists (or, once a study is closed, the place the reader was looking at, as a row and
 * how far down it, so the close changes nothing they see). Rows off the screen are laid out at a guessed height
 * (.surah-row) and the Quran face arrives late, so the row moves as the rows
 * around it take their real size: it is held in place through every such
 * change until the reader scrolls or taps for themselves. `still` is reading
 * without touching the words: a finger on them scrolls, opens and shows nothing.
 */
export default function AyahList({ listRef, ayahs, target, still, onScrolled, children: row }) {
  const rows = useDeferredValue(ayahs, ayahs.slice(0, FIRST_PAINT_ROWS))
  // A row to open at, or a row and how far down it (where the reader was looking when a study closed).
  const aimAt = typeof target === 'object' ? target?.ayah : target
  const aimInto = typeof target === 'object' ? target?.into ?? 0 : 0
  const reached = aimAt && rows.length >= aimAt
  useLayoutEffect(() => {
    const list = listRef.current
    if (!reached || !list) return undefined
    const aim = () => showRow(list, aimAt, aimInto)
    aim()
    const sizes = new ResizeObserver(aim)
    for (const one of list.children) sizes.observe(one)
    const release = () => {
      sizes.disconnect()
      TAKE_OVER.forEach((type) => document.removeEventListener(type, release, true))
    }
    TAKE_OVER.forEach((type) => document.addEventListener(type, release, { capture: true, passive: true }))
    return release
  // `target` itself, not only what is in it: a hold let go at the reader's touch is taken up again by the next
  // one even when it names the same row (the study closed over the row it was opened at).
  }, [listRef, reached, aimAt, aimInto, target])

  // Unlike other scroll panes, the surah hands a swipe on to the page at its
  // ends, so on a phone the search above is never out of reach.
  return (
    <ol
      ref={listRef}
      onScroll={(e) => onScrolled(rowAt(e.currentTarget))}
      className={`scroll-pane overscroll-y-auto flex-1 min-w-0 h-full divide-y divide-[var(--border)] ${still ? 'touch-none [&>li]:pointer-events-none' : ''}`}
    >
      {rows.map(row)}
    </ol>
  )
}
