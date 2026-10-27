/**
 * The Map: a high-level overview of the nine Islamic sciences as product-breakdown trees, and the methodologies
 * (schools and movements) beside them. A tab reached from the header's Map button and listed nowhere else (`hidden`),
 * so every screen has an address: back, forward, a reload and Copy link all land on it (lib/map/mapPlace.js).
 *
 * Three views: an index of nine cards, a chart (one science's tree, from PbsChart), and the methodologies (ManhajView),
 * a separate card below the nine since schools and movements are not a science. A box with deeper topics zooms: the
 * chart redraws with that box as root. The trail above walks back up, as does Esc. Content is lib/shell/pbsTree over
 * lib/shell/pbsData; this file holds which place is showing, and the zoom of the drawing.
 *
 * What this does NOT do yet, on purpose: nothing here tracks how far a reader has gone through a science; a
 * `progress` prop could later decorate a box in PbsChart without restructuring it.
 */
import { useEffect, useEffectEvent, useLayoutEffect, useMemo, useRef, useState } from 'react'

import ArabicText from '../ui/text/ArabicText'
import SectionHeader from '../ui/display/SectionHeader'
import ManhajView from './ManhajView'
import PbsChart from '../shell/PbsChart'
import { FAMILIES } from '../../lib/map/manhajData'
import { MANHAJ, placeOf, reachable, screenOf, upOf, valueOf } from '../../lib/map/mapPlace'
import { scrollToTop } from '../../lib/motion/scrollToEl'
import { useArrival } from '../../lib/nav/useArrival'
import { CHARTS } from '../../lib/shell/pbsData'
import { chartTree, nodeAt, viewConfig } from '../../lib/shell/pbsTree'
import { widthAtLabel } from '../../lib/shell/pbsLayout'
import { useMedia, PHONE } from '../../lib/hooks/useMedia'
import chartKnobs from '../../config/pbsChart.json'
import zoomKnobs from '../../config/zoom.json'
import ZoomBar from '../ui/inputs/ZoomBar'
import { useZoom } from '../../lib/hooks/useZoom'

// At 100% the chart never draws narrower than this; on a phone, narrower than its smallest label reading at phone-label-px.
// Either way it scrolls inside its own frame, and (the frame's padding aside) never draws its text unreadably small.
const CHART_MIN_REM = 56
const FRAME_PAD_PX = 32
const INDEX = { at: 'index' }

/** Numbered 1 to 9 by how the sciences lead into each other, in threes that belong together: the law, the sources, the language. The arrow keys walk this same order. */
const ORDER = [...CHARTS].sort((a, b) => a.id.localeCompare(b.id))

const placeAt = (value) => placeOf(value, CHARTS, FAMILIES)

/** The way back up from a place, root first, each with the place it opens; the last is where the reader is. */
function trailOf(place, chart, tree, path) {
  if (place.at === 'chart') {
    const boxes = path.map((_, n) => nodeAt(tree, path.slice(0, n + 1)))
    return [{ label: 'Map', place: INDEX }, { label: chart.en, place: { ...place, path: [] } },
      ...boxes.map((box, n) => ({ label: box.en || box.ar, place: { ...place, path: path.slice(0, n + 1) } }))]
  }
  if (place.at === MANHAJ) {
    const family = FAMILIES.find((one) => one.id === place.family)
    const group = family.groups.find((one) => one.id === place.group)
    return [{ label: 'Map', place: INDEX }, { label: 'Methodologies', place: { at: MANHAJ, family: family.id } },
      ...(group ? [{ label: group.en, place: { at: MANHAJ, family: family.id, group: group.id } }] : [])]
  }
  return []
}

export default function MapPanel({ incoming, arrival, onVisit }) {
  const [place, setPlace] = useState(() => placeAt(incoming))
  const [hoverBranch, setHoverBranch] = useState(null)
  const phone = useMedia(PHONE)
  const frame = useRef(null)
  const { zoom, size, endPinch, step, set, reset } = useZoom(frame, zoomKnobs.map, place.at === 'chart') // the index has nothing to zoom

  // Back, forward, or a link from elsewhere: show the place it names.
  // A new screen opens at its top, as a fresh page would: a group picked low in the grid used to open scrolled past
  // its own beginning. A comparison picked on a group's page is the same screen, so it stays where the reader is.
  const show = (next) => {
    if (screenOf(next) !== screenOf(place)) scrollToTop()
    if (next.at !== 'chart' || next.id !== place.id) reset()
    setPlace(next)
    setHoverBranch(null)
  }
  const { arrived } = useArrival(arrival)
  if (arrived) show(placeAt(incoming))

  const go = (next) => {
    show(next)
    onVisit?.(valueOf(next))
  }

  const chart = place.at === 'chart' ? CHARTS.find((one) => one.id === place.id) : null
  const tree = useMemo(() => (chart ? chartTree(chart) : null), [chart])
  const path = useMemo(() => (tree ? reachable(tree, place.path) : []), [tree, place.path])
  const shown = tree && nodeAt(tree, path)
  const config = useMemo(
    () => shown && viewConfig(shown, path.length ? [] : chart.config.footnote),
    [shown, path.length, chart],
  )
  // The chart's least width: on a phone, wide enough to read; elsewhere, a fixed floor.
  const minWidth = phone && config ? `${widthAtLabel(config, chartKnobs['phone-label-px']) + FRAME_PAD_PX}px` : `${CHART_MIN_REM}rem`
  // A chart opens with its root in view, not at its left edge: the drawing is centred on the root.
  const where = chart ? [chart.id, ...path].join('/') : ''
  useLayoutEffect(() => {
    const el = frame.current
    if (el) el.scrollLeft = (el.scrollWidth - el.clientWidth) / 2
  }, [where, phone])
  const trail = trailOf(place, chart, tree, path)
  const endOfTrail = useRef(null)
  useLayoutEffect(() => { if (endOfTrail.current) endOfTrail.current.scrollLeft = endOfTrail.current.scrollWidth }, [trail.length, place])

  // On the whole page while the Map shows (a hidden tab's effects are torn down), not only with focus inside it:
  // a click on plain text leaves the focus on the page's body.
  const press = useEffectEvent((e) => {
    if (e.defaultPrevented || e.target.closest?.('input, select, textarea, dialog')) return // a field's or a sheet's own keys
    if (e.key === 'Escape' && place.at !== 'index') { e.preventDefault(); go(upOf({ ...place, path })); return }
    // The arrows scroll a chart that is focused; anywhere else on the page they walk the sciences.
    if (!chart || frame.current?.contains(e.target)) return
    const i = ORDER.findIndex((one) => one.id === chart.id)
    if (e.key === 'ArrowRight' && i < ORDER.length - 1) go({ at: 'chart', id: ORDER[i + 1].id, path: [] })
    if (e.key === 'ArrowLeft' && i > 0) go({ at: 'chart', id: ORDER[i - 1].id, path: [] })
  })
  useEffect(() => {
    const onKey = (e) => press(e)
    addEventListener('keydown', onKey)
    return () => removeEventListener('keydown', onKey)
  }, [])

  const header = chart
    ? { title: chart.en, arabic: chart.ar, subtitle: `Frame: ${chart.frame}. A box marked › has more inside; tap it to zoom in.` }
    : place.at === MANHAJ
      ? { title: 'Methodologies', arabic: 'المناهج', subtitle: 'Creed schools, schools of law, Sufi orders and modern movements: what each holds, and where they differ.' }
      : { subtitle: 'Nine sciences, one frame per chart. Open one to see its parts, and zoom into any box with more inside.' }

  return (
    <div className="panel">
      <SectionHeader tab="map" history={false} {...header} />

      {trail.length > 0 && (
        <nav aria-label="Map trail" className="flex items-center gap-2 type-ui text-[var(--text-dim)]">
          <button type="button" onClick={() => go(upOf({ ...place, path }))} className="icon-button shrink-0" aria-label="Up one level" title="Up one level (Esc)">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 18l-6-6 6-6" /></svg>
          </button>
          {/* Each step at its full name: on a phone the row scrolls sideways, kept at its end, where the reader is. */}
          <ol ref={endOfTrail} className="flex flex-1 min-w-0 items-center gap-x-1.5 gap-y-1 overflow-x-auto whitespace-nowrap sm:flex-wrap">
            {trail.map((step, n) => (
              <li key={n} className="flex shrink-0 items-center gap-1.5">
                {n > 0 && <span aria-hidden="true" className="text-[var(--text-faint)]">›</span>}
                {n === trail.length - 1 ? (
                  <span aria-current="page" className="font-semibold text-[var(--text)]">{step.label}</span>
                ) : (
                  <button type="button" onClick={() => go(step.place)} className="underline decoration-dotted underline-offset-4 hover:text-[var(--text)]">
                    {step.label}
                  </button>
                )}
              </li>
            ))}
          </ol>
          {chart && <ZoomBar zoom={zoom} knobs={zoomKnobs.map} onStep={step} onSet={set} onReset={reset} />}
        </nav>
      )}

      {chart ? (
        <div
          ref={frame}
          onTouchEnd={endPinch}
          onTouchCancel={endPinch}
          className="relative overflow-auto rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] h-[max(24rem,calc(100dvh-var(--app-header-h,4rem)-14rem))]"
          tabIndex={0}
          role="region"
          aria-label={`${chart.en} chart`}
        >
          <div className="p-4" style={size(minWidth)}>
            <PbsChart
              key={path.join('.')}
              config={config}
              activeBranch={hoverBranch}
              onHoverBranch={setHoverBranch}
              onZoom={(rel) => go({ ...place, path: [...path, ...rel] })}
            />
          </div>
        </div>
      ) : place.at === MANHAJ ? (
        <ManhajView place={place} onGo={go} />
      ) : (
        <MapIndex onGo={go} />
      )}
    </div>
  )
}

/** The nine-card overview: one science per card, click opens its chart; the methodologies card sits apart below.
 * Number, English and frame read down the left, the Arabic name large on the right. */
function MapIndex({ onGo }) {
  return (
    <div className="flex flex-col gap-5">
      <div className="grid gap-5 grid-cols-[repeat(auto-fill,minmax(18rem,1fr))]">
        {ORDER.map((chart, delay) => (
          <IndexCard key={chart.id} label={chart.id} ar={chart.ar} en={chart.en} note={chart.frame} color={chart.accent}
            className="pbs-rise border-r-4" style={{ borderRightColor: chart.accent, '--d': `${delay * 55}ms` }}
            onClick={() => onGo({ at: 'chart', id: chart.id, path: [] })} />
        ))}
      </div>
      <IndexCard label="Beyond the sciences" ar="المناهج والفِرَق"
        en="Methodologies: creed schools, schools of law, Sufi orders, modern movements"
        note="Core beliefs of each, and where they differ"
        className="border-dashed border-[var(--border-hi)]" onClick={() => onGo({ at: MANHAJ, family: FAMILIES[0].id })} />
    </div>
  )
}

function IndexCard({ label, ar, en, note, color, className, style, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`pbs-card flex items-center justify-between gap-4 text-left p-4 rounded-[var(--radius-md)] border
        border-[var(--border)] bg-[var(--surface-hi)] ${className}`}
      style={style}
    >
      <span className="pbs-go text-[var(--text-faint)]" aria-hidden="true">↗</span>
      <span className="flex-1 min-w-[8rem] space-y-1">
        <span className="block eyebrow tabular-nums">{label}</span>
        <span className="block type-body font-semibold text-[var(--text)]">{en}</span>
        <span className="block type-ui text-[var(--text-dim)]">{note}</span>
      </span>
      {/* Takes what the English (min 8rem) leaves: a name too long for that (القواعد الفقهية) breaks
          between its words onto two lines instead of squeezing the English to a word per line. */}
      <ArabicText as="span" size="lg" className="arabic-inline min-w-0 text-right" style={color ? { color } : undefined}>{ar}</ArabicText>
    </button>
  )
}
