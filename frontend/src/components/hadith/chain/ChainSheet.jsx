/**
 * The pop-up for one hadith's chain, in tabs of what there is to read: the chain drawn (hadith/chain/ChainDrawing, weak
 * narrators marked and doubtful links lettered on it), the weak points ranked (hadith/chain/WeakPoints, `weak` from
 * hadith/chain/weak, `linkPoints` the doubtful links), what classical books say of the hadith (`rulings`, hadith/chain/ScholarRulings)
 * and the words between its narrators with the terms of the science (hadith/chain/TermGuide). A tab with nothing to show is
 * left out, a hadith with no chain to draw (`chainless`) has no Chain tab, and opened from the reading options with
 * no hadith it is the words alone, with no tabs.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { usulGuideQuery } from '../../../api'
import { CHAIN } from '../../../lib/hadith/hadithWords'

import BottomSheet from '../../ui/overlays/BottomSheet'
import ChainDrawing from './ChainDrawing'
import SheetHeader from '../../ui/overlays/SheetHeader'
import Segmented from '../../ui/inputs/Segmented'
import ScholarRulings from './ScholarRulings'
import TermGuide from './TermGuide'
import WeakPoints from './WeakPoints'

// Each tab's name, and the sheet's title while it is open.
const PARTS = {
  chain: { tab: 'Chain', title: 'The chain' },
  weak: { tab: 'Weak points', title: 'Where it may be weak' },
  verdicts: { tab: 'Verdicts', title: 'What scholars said' },
  words: { tab: 'Words', title: 'Words and terms' },
}

export default function ChainSheet({ links = null, author = '', weak = [], linkPoints = [], rulings = [], scale = [], chainless = false, onClose, accent, onNarrator }) {
  const tabs = [
    links && !chainless && 'chain',
    weak.length + linkPoints.length > 0 && 'weak',
    rulings.length > 0 && 'verdicts',
    'words',
  ].filter(Boolean)
  const [picked, setPicked] = useState(tabs[0])
  const tab = tabs.includes(picked) ? picked : tabs[0]
  const { data: guide } = useQuery(usulGuideQuery)

  return (
    <BottomSheet label={PARTS[tab].title} onClose={onClose} className="max-h-[var(--sheet-tall)] flex flex-col">
      <SheetHeader onClose={onClose}>
        <h2 aria-live="polite" className="type-ui font-semibold text-[var(--text)]">{PARTS[tab].title}</h2>
      </SheetHeader>
      {tabs.length > 1 && (
        <div className="px-5 pb-3">
          <Segmented
            label="Parts of this hadith"
            fill
            compact
            accent={accent}
            value={tab}
            onChange={setPicked}
            options={tabs.map((id) => ({ id, label: PARTS[id].tab }))}
          />
        </div>
      )}
      <div className="overflow-y-auto px-5 pb-5">
        {tab === 'chain' && <ChainDrawing links={links} author={author} weak={weak} linkPoints={linkPoints} onNarrator={onNarrator} />}
        {tab === 'weak' && <WeakPoints points={weak} linkPoints={linkPoints} scale={scale} onNarrator={onNarrator} />}
        {tab === 'verdicts' && <ScholarRulings rulings={rulings} accent={accent} />}
        {tab === 'words' && <TermGuide groups={[...CHAIN.terms.groups, ...(guide?.glossary ?? [])]} />}
      </div>
    </BottomSheet>
  )
}
