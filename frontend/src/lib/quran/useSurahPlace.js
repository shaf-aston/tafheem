import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

import { FIRST_SURAH, LAST_SURAH } from './surahRef'
import { useMedia } from '../hooks/useMedia'
import { scrollToEl } from '../motion/scrollToEl'
import { rowAt, showRow } from './surahRows'
import { useSlide, useSwipe } from '../motion/useSwipe'
import QURAN from '../../config/quran.json'

const { split: SPLIT } = QURAN
const { full: FULL } = SPLIT
// Wide enough for the surah and the study side by side; Tailwind's lg.
const TWO_PANES = '(min-width: 64rem)'

/**
 * Where the Quran reader is: the surah and ayah (`place`, owned by the caller
 * and changed through `onPlace`), the ayah at the top of the list as it is
 * scrolled, and on a narrow screen how the surah and the study share it. Also
 * the ways to move: the keys, a swipe, and the study's sheet. `data` is the
 * surah once it has come, from useSurahReading.
 */
export function useSurahPlace({ surah, ayah }, data, onPlace, onClose) {
  const twoPanes = useMedia(TWO_PANES)

  const list = useRef(null)
  // The ayah at the top of the list as it is scrolled: the rail follows it.
  const [here, setHere] = useState(ayah ?? 1)
  // A row tapped is already in view; only an ayah opened from elsewhere is
  // scrolled to.
  const [tapped, setTapped] = useState(null)
  const [hereIn, setHereIn] = useState(surah)
  if (hereIn !== surah) { setHereIn(surah); setHere(ayah ?? 1); setTapped(null) }
  // Narrow, an ayah studied splits the reader in two, one over the other;
  // `share` is how much of it the surah keeps.
  const stacked = !twoPanes && Boolean(ayah)
  const panes = useRef(null)
  const [share, setShare] = useState(SPLIT.share)
  // Splitting brings the two panes up to fill the screen, the ayah at the top
  // of its half: the half it was in may end above it.
  const wasStacked = useRef(false)
  useEffect(() => {
    if (!stacked) wasStacked.current = false
    if (!stacked || !data || wasStacked.current) return
    wasStacked.current = true
    scrollToEl(panes.current, 'top')
    showRow(list.current, ayah)
  }, [stacked, ayah, data])
  const goTo = useCallback((n) => { showRow(list.current, n); setHere(n) }, [])
  const open = (n) => { setTapped(n); onPlace({ surah, ayah: n }) }
  // Closing the study hands its half back to the surah: the list is taller and the page under it
  // shorter, and none of that may move what is being read. The row at the top is noted on the way
  // out and put back if the change disturbed it, so a close never lands anywhere else.
  const resting = useRef(null)
  useLayoutEffect(() => {
    const row = resting.current
    if (stacked || row === null) return
    resting.current = null
    if (list.current && rowAt(list.current) !== row) { showRow(list.current, row); setHere(row) }
  }, [stacked])
  // Focus goes back to the ayah's row, not lost with the close button. The sheet is given back its
  // usual size if it had been taken full screen, or it would open full screen next time; a size the reader dragged to is kept.
  const shut = useCallback(() => {
    resting.current = stacked && list.current ? rowAt(list.current) : null
    setShare((now) => (now <= FULL ? SPLIT.share : now))
    onPlace({ surah, ayah: null })
    list.current?.children[ayah - 1]?.querySelector('[role="button"]')?.focus({ preventScroll: true })
  }, [onPlace, surah, ayah, stacked])
  const changeSurah = useCallback((n) => onPlace({ surah: n, ayah: null }), [onPlace])

  // ← → change surah and Esc shuts the study, then the reader. Not while typing,
  // and not while a sheet is open: it handles its own Esc.
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return
      // Arrows belong to whatever has its own: a field, a strip, a row of choices.
      if (e.target.closest('input, textarea, select, .strip-x, [role="group"]') || document.querySelector('dialog[open]')) return
      if (e.key === 'ArrowLeft' && surah > FIRST_SURAH) changeSurah(surah - 1)
      if (e.key === 'ArrowRight' && surah < LAST_SURAH) changeSurah(surah + 1)
      if (e.key === 'Escape') (ayah ? shut : onClose)()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [surah, ayah, changeSurah, shut, onClose])
  const swipe = useSwipe(surah > FIRST_SURAH && (() => changeSurah(surah - 1)),
    surah < LAST_SURAH && (() => changeSurah(surah + 1)))
  const slide = useSlide(surah)

  // On a phone the study is a sheet: its tabs, and a word or a tab that needs
  // room, ask the sheet for the whole screen. Stepping scrolls the surah to the ayah.
  // Stepping is not a tap on a row, so the list follows it, back onto the ayah first tapped as much as any other.
  const step = (n) => { setTapped(null); onPlace({ surah, ayah: n }) }
  const sheet = stacked && {
    onFull: () => setShare(FULL),
    onPrev: ayah > 1 ? () => step(ayah - 1) : null,
    onNext: ayah < data?.ayah_count ? () => step(ayah + 1) : null,
  }

  return {
    twoPanes, stacked, list, here, setHere, tapped, panes, share, setShare,
    goTo, open, shut, changeSurah, swipe, slide, sheet,
  }
}
