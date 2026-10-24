/**
 * The pop-up for chains: one hadith's chain drawn (hadith/ChainDrawing), or the
 * guide (hadith/TermGuide) to the words between its narrators and then the terms of the science. Opened on the
 * drawing from a hadith card, where a link turns it to the guide and back;
 * opened from the reading options with no hadith, it is the guide alone.
 * Where the chain has weak narrators (`weak`, from lib/weak) their boxes are
 * marked in the drawing and a ranked list (hadith/WeakPoints) follows it; doubtful
 * links (`linkPoints`) are marked on their rungs and listed after the narrators. What classical books say of
 * the hadith (`rulings`) comes last (hadith/ScholarRulings). A hadith with no chain to draw (`chainless`) gets
 * that alone.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { usulGuideQuery } from '../../api'
import { CHAIN } from '../../lib/hadith/hadithWords'

import BottomSheet from '../ui/BottomSheet'
import ChainDrawing from './ChainDrawing'
import CloseButton from '../ui/CloseButton'
import ScholarRulings from './ScholarRulings'
import SheetLink from './SheetLink'
import TermGuide from './TermGuide'
import WeakPoints from './WeakPoints'

export default function ChainSheet({ links = null, author = '', weak = [], linkPoints = [], rulings = [], scale = [], chainless = false, onClose, accent, onNarrator }) {
  const [words, setWords] = useState(!links)
  const { data: guide } = useQuery(usulGuideQuery)
  const title = words ? 'Words and terms' : chainless ? 'This hadith' : 'The chain'

  return (
    <BottomSheet label={title} onClose={onClose} className="max-h-[var(--sheet-tall)] flex flex-col">
      <header className="flex items-center justify-between gap-3 px-5 pt-4 pb-3">
        <h2 aria-live="polite" className="type-ui font-semibold text-[var(--text)]">{title}</h2>
        <span className="flex items-center gap-3">
          {links && !chainless && (
            <SheetLink accent={accent} onClick={() => setWords(!words)}>
              {words ? 'Back to the chain' : 'What the words mean'}
            </SheetLink>
          )}
          <CloseButton onClick={onClose} className="shrink-0" />
        </span>
      </header>
      <div className="overflow-y-auto px-5 pb-5">
        {words ? <TermGuide groups={[...CHAIN.terms.groups, ...(guide?.glossary ?? [])]} /> : (
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
