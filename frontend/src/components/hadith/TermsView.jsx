/**
 * The words of the science as a tree, opened from the hadith More menu. A screen as wide as the whole tree needs
 * at its smallest legible scale (lib/termsChart wholeWidth, never under theme.json's terms-tree-min) draws every
 * group and term at once (shell/PbsChart); a narrower one lists the groups, each with the question it splits on,
 * and a tap lists that group's terms as stacked chips, a term's kids indented under it. The chart never draws below
 * MIN_SCALE, so where it still overflows its frame scrolls, its far edge fading. A tap on any term opens its card
 * (hadith/TermCard).
 */
import { useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { usulGuideQuery } from '../../api'
import { layoutChart } from '../../lib/shell/pbsLayout'
import { branchChart, MIN_SCALE, termAt, termsChart, wholeWidth } from '../../lib/hadith/termsChart'
import { useZoom } from '../../lib/hooks/useZoom'
import { useOpenAtTop } from '../../lib/motion/scrollToEl'
import { atLeast, SHELL_MAX, TERMS_TREE_MIN, useMedia } from '../../lib/hooks/useMedia'

import ArabicText from '../ui/ArabicText'
import EmptyState from '../ui/EmptyState'
import ErrorAlert from '../ui/ErrorAlert'
import { AnalyzerSkeleton } from '../ui/Skeleton'
import SheetLink from './SheetLink'
import Tile from '../ui/Tile'
import PbsChart from '../shell/PbsChart'
import ZoomBar from '../ui/ZoomBar'
import zoomKnobs from '../../config/zoom.json'
import TermCard from './TermCard'

/**
 * A chart in a frame that scrolls both ways: at 100% it is fitted to the frame, never narrower than MIN_SCALE draws it,
 * and the zoom bar (pinch, Ctrl/⌘ + wheel and the + − 0 keys too) takes it from the whole tree down to a single box.
 */
function Chart({ config, onZoom }) {
  const { width } = useMemo(() => layoutChart(config), [config])
  const frame = useRef(null)
  const { zoom, pinching, endPinch, step, set, reset } = useZoom(frame, zoomKnobs.terms)
  return (
    <div className="space-y-2">
      <div className="flex justify-end type-small text-[var(--text-dim)]">
        <ZoomBar zoom={zoom} knobs={zoomKnobs.terms} onStep={step} onSet={set} onReset={reset} />
      </div>
      <div
        ref={frame}
        onTouchEnd={endPinch}
        onTouchCancel={endPinch}
        className="scroll-fade-x max-h-[max(24rem,calc(100dvh-var(--app-header-h,4rem)-14rem))] overflow-y-auto"
        tabIndex={0}
        role="region"
        aria-label="Terms chart"
      >
        <div style={{ width: `max(${zoom * 100}%, ${Math.round(width * MIN_SCALE * zoom)}px)`, transition: pinching ? 'none' : 'width calc(var(--motion-base-ms) * 1ms) ease' }}>
          <PbsChart config={config} onZoom={onZoom} />
        </div>
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

// `group` is the group drawn alone (the place's "terms/<n>", HadithPanel owns it), `onGroup(n | null)` changes it.
export default function TermsView({ accent, onOpen, group = null, onGroup }) {
  useOpenAtTop()
  const { data: guide, isPending, isError, error, refetch } = useQuery(usulGuideQuery)
  const [picked, setPicked] = useState(null) // Arabic name of the term whose card is open
  const glossary = useMemo(() => guide?.glossary ?? [], [guide])
  const whole = useMemo(() => termsChart(glossary), [glossary])
  // The whole tree from the width it draws at its smallest legible scale, never below the floor and never past the
  // page's own widest (the shell stops growing there, so a wider screen would not show it any more of the tree).
  const wide = useMedia(atLeast(glossary.length ? Math.max(TERMS_TREE_MIN, Math.min(wholeWidth(whole), SHELL_MAX)) : TERMS_TREE_MIN))
  const alone = useMemo(() => (group != null && glossary[group] ? branchChart(glossary, group) : null), [glossary, group])
  const found = picked && termAt(glossary, picked)

  // A tap on a box of the whole tree: a group's name draws that group, a term opens its card.
  const onWhole = ([i, j]) => (j == null ? onGroup(i) : setPicked(glossary[i].terms[j].arabic))
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
          <SheetLink accent={accent} onClick={() => onGroup(null)}>{wide ? '← The whole tree' : '← All groups'}</SheetLink>
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
            <Tile key={g.title} variant="chip" accent={accent} onClick={() => onGroup(i)} style={{ '--i': i }} className="items-start py-2">
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
