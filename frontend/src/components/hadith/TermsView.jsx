/**
 * The words of the science as a tree, opened from the hadith More menu. A screen 1100px wide or more draws every
 * group and term at once (shell/PbsChart over lib/termsChart); a narrower one lists the groups, each with the
 * question it splits on, and a tap lists that group's terms as stacked chips, a term's kids indented under it
 * (a sideways chart does not fit a phone). The chart never draws below lib/termsChart's MIN_SCALE, so a wide tree scrolls in its frame
 * rather than shrinking its words. A tap on any term opens its card (hadith/TermCard).
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { usulGuideQuery } from '../../api'
import { layoutChart } from '../../lib/pbsLayout'
import { branchChart, MIN_SCALE, termAt, termsChart } from '../../lib/termsChart'
import { useOpenAtTop } from '../../lib/scrollToEl'
import { TERMS_TREE, useMedia } from '../../lib/useMedia'

import ArabicText from '../ui/ArabicText'
import EmptyState from '../ui/EmptyState'
import ErrorAlert from '../ui/ErrorAlert'
import { AnalyzerSkeleton } from '../ui/Skeleton'
import SheetLink from '../ui/SheetLink'
import Tile from '../ui/Tile'
import PbsChart from '../shell/PbsChart'
import TermCard from './TermCard'

/** A chart in a frame that scrolls sideways once the chart would draw below MIN_SCALE. */
function Chart({ config, onZoom }) {
  const { width } = useMemo(() => layoutChart(config), [config])
  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Terms chart">
      <div style={{ minWidth: `${Math.round(width * MIN_SCALE)}px` }}>
        <PbsChart config={config} onZoom={onZoom} />
      </div>
    </div>
  )
}

/** One term as a chip, English left and Arabic right as the sections menu draws its chips; a kid is smaller and indented. */
function TermChip({ term, accent, index, small, onClick }) {
  return (
    <Tile variant="chip" accent={accent} onClick={onClick} style={{ '--i': index }} className={small ? 'ms-6 min-h-9' : ''}>
      <span className={`${small ? 'type-small' : 'type-ui font-semibold'} min-w-0`}>{term.en}</span>
      <ArabicText size={small ? 'sm' : 'lg'} className="shrink-0 leading-tight text-[var(--c)]">{term.arabic}</ArabicText>
    </Tile>
  )
}

export default function TermsView({ accent, onOpen }) {
  useOpenAtTop()
  const { data: guide, isPending, isError, error, refetch } = useQuery(usulGuideQuery)
  const wide = useMedia(TERMS_TREE)
  const [group, setGroup] = useState(null)   // index of the group drawn alone
  const [picked, setPicked] = useState(null) // Arabic name of the term whose card is open
  const glossary = useMemo(() => guide?.glossary ?? [], [guide])
  const whole = useMemo(() => termsChart(glossary), [glossary])
  const alone = useMemo(() => (group != null && glossary[group] ? branchChart(glossary, group) : null), [glossary, group])
  const found = picked && termAt(glossary, picked)

  // A tap on a box of the whole tree: a group's name draws that group, a term opens its card.
  const onWhole = ([i, j]) => (j == null ? setGroup(i) : setPicked(glossary[i].terms[j].arabic))
  // In one group, wide: a box is a term, a box under it is one of that term's kinds.
  const onAlone = ([i, j]) => {
    const term = glossary[group].terms[i]
    setPicked((j == null ? term : term.kids[j]).arabic)
  }

  return (
    <div className="space-y-3">
      {isPending && <AnalyzerSkeleton />}
      {isError && <ErrorAlert title="Could not load the terms" error={error} fallback="The terms could not be reached." onRetry={refetch} />}
      {guide && !glossary.length && <EmptyState>No terms are built yet.</EmptyState>}
      {alone && (
        <div className="flex items-baseline justify-between gap-3">
          <SheetLink accent={accent} onClick={() => setGroup(null)}>{wide ? '← The whole tree' : '← All groups'}</SheetLink>
          <p className="type-ui font-semibold text-[var(--text)] m-0">{glossary[group].title}</p>
        </div>
      )}
      {alone && !wide && <p className="type-small text-[var(--text-dim)] m-0">{glossary[group].by}</p>}
      {alone && (wide ? <Chart key={group} config={alone} onZoom={onAlone} /> : (
        <div className="grid gap-2">
          {glossary[group].terms.map((t, i) => (
            <div key={t.arabic} className="grid gap-2">
              <TermChip term={t} accent={accent} index={i} onClick={() => setPicked(t.arabic)} />
              {t.kids?.map((k) => (
                <TermChip key={k.arabic} term={k} accent={accent} index={i} small onClick={() => setPicked(k.arabic)} />
              ))}
            </div>
          ))}
        </div>
      ))}
      {!alone && glossary.length > 0 && (wide ? (
        <Chart config={whole} onZoom={onWhole} />
      ) : (
        <div className="grid gap-2">
          {glossary.map((g, i) => (
            <Tile key={g.title} variant="chip" accent={accent} onClick={() => setGroup(i)} style={{ '--i': i }} className="items-start py-2">
              <span className="min-w-0">
                <span className="block type-ui font-semibold">{g.title}</span>
                {g.by && <span className="block type-small text-[var(--text-dim)]">{g.by}</span>}
              </span>
              <ArabicText size="lg" className="shrink-0 leading-tight text-[var(--c)]">{g.name}</ArabicText>
            </Tile>
          ))}
        </div>
      ))}
      {found && (
        <TermCard
          term={found.term}
          group={found.group}
          glossary={glossary}
          accent={accent}
          onClose={() => setPicked(null)}
          onOpen={onOpen}
          onTerm={setPicked}
        />
      )}
    </div>
  )
}
