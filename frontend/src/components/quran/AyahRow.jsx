import { ayahEnd } from '../../lib/ayahEnd'
import { useRecitedWord } from '../../lib/useRecitedWord'

import GlossedAyah from './GlossedAyah'

/**
 * One ayah of the surah: its line, closed by its numbered medallion, and its
 * English the full width under it. A row of its own because it asks which of
 * its words is being recited; all but the one sounding answer with a single
 * comparison.
 */
export default function AyahRow({ ayah, english, glosses, learnt, allMeanings, src, segments, open, onOpen }) {
  const lit = useRecitedWord(src, segments)
  return (
    <li className="surah-row">
      {/* Not a <button>: text inside a button cannot be dragged over to select. The
          row still opens on a click and on Enter or Space, but a click that ends a
          drag-select (some text is selected) is the end of the selection, not a tap. */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => { if (window.getSelection()?.isCollapsed ?? true) onOpen(ayah.ayah) }}
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
        <GlossedAyah arabic={ayah.arabic} english={glosses} learnt={learnt} allMeanings={allMeanings} lit={lit} end={ayahEnd(ayah.ayah)} />
        {english && (
          <span className="block type-body text-[var(--text)] leading-relaxed border-t border-[var(--border)] pt-2">
            {english}
          </span>
        )}
      </div>
    </li>
  )
}
