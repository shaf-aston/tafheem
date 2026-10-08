/**
 * The pop-up for chains: one hadith's chain drawn (ui/ChainDrawing), or the
 * guide to the words between its narrators (ui/ChainWords). Opened on the
 * drawing from a hadith card, where a link turns it to the guide and back;
 * opened from the reading options with no hadith, it is the guide alone.
 * Where the chain has weak narrators (`weak`, from lib/weak) their boxes are
 * marked in the drawing and a ranked list (ui/WeakPoints) follows it; doubtful
 * links (`linkPoints`) are marked on their rungs and listed after the narrators. What classical books say of
 * the hadith (`rulings`) comes last (ui/ScholarRulings). A hadith with no chain to draw (`chainless`) gets
 * that alone.
 */
import { useState } from 'react'

import BottomSheet from './BottomSheet'
import ChainDrawing from './ChainDrawing'
import ChainWords from './ChainWords'
import CloseButton from './CloseButton'
import ScholarRulings from './ScholarRulings'
import WeakPoints from './WeakPoints'

export default function ChainSheet({ links = null, author = '', weak = [], linkPoints = [], rulings = [], scale = [], chainless = false, onClose, accent, onNarrator }) {
  const [words, setWords] = useState(!links)
  const title = words ? 'Chain words' : chainless ? 'This hadith' : 'The chain'

  return (
    <BottomSheet label={title} onClose={onClose} className="max-h-[var(--sheet-tall)] flex flex-col">
      <header className="flex items-center justify-between gap-3 px-5 pt-4 pb-3">
        <h2 aria-live="polite" className="type-ui font-semibold text-[var(--text)]">{title}</h2>
        <span className="flex items-center gap-3">
          {links && !chainless && (
            <button
              type="button"
              onClick={() => setWords(!words)}
              className="press type-small text-[var(--text-dim)] hover:text-[var(--c)] underline underline-offset-4 decoration-dotted"
              style={{ '--c': accent }}
            >
              {words ? 'Back to the chain' : 'What the words mean'}
            </button>
          )}
          <CloseButton onClick={onClose} className="shrink-0" />
        </span>
      </header>
      <div className="overflow-y-auto px-5 pb-5">
        {words ? <ChainWords /> : (
          <>
            {!chainless && <ChainDrawing links={links} author={author} weak={weak} linkPoints={linkPoints} onNarrator={onNarrator} />}
            {!chainless && <WeakPoints points={weak} linkPoints={linkPoints} scale={scale} onNarrator={onNarrator} />}
            <ScholarRulings rulings={rulings} accent={accent} />
          </>
        )}
      </div>
    </BottomSheet>
  )
}
