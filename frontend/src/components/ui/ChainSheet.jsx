/**
 * The pop-up for chains: one hadith's chain drawn (ui/ChainDrawing), or the
 * guide to the words between its narrators (ui/ChainWords). Opened on the
 * drawing from a hadith card, where a link turns it to the guide and back;
 * opened from the reading options with no hadith, it is the guide alone.
 */
import { useState } from 'react'

import BottomSheet from './BottomSheet'
import ChainDrawing from './ChainDrawing'
import ChainWords from './ChainWords'
import CloseButton from './CloseButton'

export default function ChainSheet({ links = null, author = '', onClose, accent }) {
  const [words, setWords] = useState(!links)
  const title = words ? 'Chain words' : 'The chain'

  return (
    <BottomSheet label={title} onClose={onClose} className="max-h-[85dvh] flex flex-col">
      <header className="flex items-center justify-between gap-3 px-5 pt-4 pb-3">
        <h2 aria-live="polite" className="type-ui font-semibold text-[var(--text)]">{title}</h2>
        <span className="flex items-center gap-3">
          {links && (
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
        {words ? <ChainWords /> : <ChainDrawing links={links} author={author} />}
      </div>
    </BottomSheet>
  )
}
