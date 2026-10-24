import { useState } from 'react'

import { ayahEnd } from '../../lib/quran/ayahEnd'
import { useRecitedWord } from '../../lib/quran/useRecitedWord'

import GlossedAyah from './GlossedAyah'

/**
 * One ayah of the surah: its line, closed by its numbered medallion, and its
 * English the full width under it. A row of its own because it asks which of
 * its words is being recited; all but the one sounding answer with a single
 * comparison.
 */
export default function AyahRow({ ayah, english, glosses, learnt, allMeanings, src, segments, open, onOpen }) {
  const lit = useRecitedWord(src, segments)
  // A touch screen has no hover, so a tap on a word shows its meaning first; a
  // second tap on the same word, or a tap anywhere else, opens the ayah.
  const [peek, setPeek] = useState(-1)
  const tap = (e) => {
    if (!(window.getSelection()?.isCollapsed ?? true)) return
    const word = e.target.closest?.('.gloss-word[data-gloss]')
    const i = word ? Number(word.dataset.i) : -1
    if (i >= 0 && i !== peek && window.matchMedia?.('(pointer: coarse)').matches) { setPeek(i); return }
    setPeek(-1)
    onOpen(ayah.ayah)
  }
  return (
    <li className="surah-row">
      {/* Not a <button>: text inside a button cannot be dragged over to select. The
          row still opens on a click and on Enter or Space, but a click that ends a
          drag-select (some text is selected) is the end of the selection, not a tap. */}
      <div
        role="button"
        tabIndex={0}
        onClick={tap}
        onKeyDown={(e) => {
          if (e.target !== e.currentTarget || (e.key !== 'Enter' && e.key !== ' ')) return
          e.preventDefault()
          onOpen(ayah.ayah)
        }}
        aria-pressed={open}
        className={`w-full text-left p-4 space-y-2 transition-colors hover:bg-[var(--surface-hi)]
          focus:outline-none focus-visible:bg-[var(--surface-hi)]
          ${open ? 'bg-[color-mix(in_srgb,var(--c)_8%,transparent)] shadow-[inset_0_0_0_1px_color-mix(in_srgb,var(--c)_35%,transparent)]' : ''}`}
      >
        <GlossedAyah arabic={ayah.arabic} english={glosses} learnt={learnt} allMeanings={allMeanings} lit={lit} peek={peek} end={ayahEnd(ayah.ayah)} />
        {english && (
          <span className="block type-body text-[var(--text)] leading-relaxed border-t border-[var(--border)] pt-2">
            {english}
          </span>
        )}
      </div>
    </li>
  )
}
