/**
 * The Map: a high-level overview of the nine Islamic sciences as
 * product-breakdown trees, opened from the header like Settings — not a tab,
 * so it never lives in the tab strip or the URL.
 *
 * Three views inside one dialog: an index of nine cards, a chart view (one
 * science's tree, from PbsChart), and the methodologies view (ManhajView), a
 * separate card below the nine since schools and movements are not a science. A box with deeper topics zooms: the chart
 * redraws with that box as root, and a breadcrumb walks back up. Content is
 * lib/pbsTree over lib/shell/pbsData; this file only holds which view and which
 * zoom path are showing.
 *
 * A native <dialog> is used for the same reason as SettingsPanel: focus
 * trapping, Esc and the backdrop come free from the browser.
 *
 * What this does NOT do yet, on purpose: nothing here tracks how far a reader
 * has gone through a science; a `progress` prop could later decorate a box in
 * PbsChart without restructuring it.
 */
import { useCallback, useLayoutEffect, useMemo, useRef, useState } from 'react'

import ArabicText from '../ui/ArabicText'
import ManhajView from './ManhajView'
import PbsChart from './PbsChart'
import { closeOnBackdrop, useModal } from '../../lib/hooks/useModal'
import { anchoredScroll, pinchedZoom, usePinch } from '../../lib/shell/usePinch'
import { CHARTS } from '../../lib/shell/pbsData'
import { chartTree, nodeAt, viewConfig } from '../../lib/shell/pbsTree'

const ZOOM_MIN = 0.7
const ZOOM_MAX = 3
const ZOOM_STEP = 0.2
// At 100% the chart never draws narrower than this, so on a phone its text stays readable and the chart scrolls inside its own frame.
const CHART_MIN_REM = 56
// The methodologies view's id; never a chart id, so `current` stays null there.
const MANHAJ = 'manhaj'

export default function MapPanel({ open, onClose }) {
  const dialog = useModal(open)
  const [currentId, setCurrentId] = useState(null)
  const [path, setPath] = useState([]) // child indices from the chart root to the zoomed box
  const [hoverBranch, setHoverBranch] = useState(null)
  const [zoom, setZoom] = useState(1)
  const [pinching, setPinching] = useState(false)
  const frame = useRef(null)
  const anchor = useRef(null) // { x, y, ratio }: the spot to keep under the fingers once the new zoom is drawn

  // A pinch on the chart zooms the chart, never the page. The spot between the fingers stays put:
  // the content grows by `ratio` around it, so the scroll moves by the same amount.
  const pinch = useCallback((by, x, y) => {
    setPinching(true)
    setZoom((z) => {
      const next = pinchedZoom(z, by, ZOOM_MIN, ZOOM_MAX)
      anchor.current = { x, y, ratio: next / z }
      return next
    })
  }, [])
  useLayoutEffect(() => {
    const el = frame.current
    const a = anchor.current
    if (!el || !a) return
    el.scrollLeft = anchoredScroll(el.scrollLeft, a.x, a.ratio)
    el.scrollTop = anchoredScroll(el.scrollTop, a.y, a.ratio)
    anchor.current = null
  }, [zoom])

  // Reopening should not resume where a previous visit left off: reset on the
  // way out, once the dialog has actually closed (Esc, backdrop, or the
  // header's own close button all end here via the native `close` event).
  const handleDialogClose = () => {
    setCurrentId(null)
    setPath([])
    setHoverBranch(null)
    setZoom(1)
    onClose()
  }

  const current = CHARTS.find((c) => c.id === currentId) ?? null
  usePinch(frame, current ? pinch : null) // the index has nothing to zoom
  const showManhaj = currentId === MANHAJ
  const tree = useMemo(() => (current ? chartTree(current) : null), [current])
  const shown = tree && (nodeAt(tree, path) ?? tree)
  const config = useMemo(
    () => shown && viewConfig(shown, path.length ? [] : current.config.footnote),
    [shown, path.length, current],
  )
  // Every level's name, root first, for the breadcrumb.
  const trail = tree ? path.map((_, n) => nodeAt(tree, path.slice(0, n + 1))) : []

  const goIndex = () => { setCurrentId(null); setPath([]); setHoverBranch(null) }
  const goChart = (id) => { setCurrentId(id); setPath([]); setHoverBranch(null) }
  const goUp = () => { if (path.length) { setPath(path.slice(0, -1)); setHoverBranch(null) } else goIndex() }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      if (current) { e.preventDefault(); goUp(); return }
      if (showManhaj) { e.preventDefault(); goIndex(); return }
      return // let the dialog's own Escape close it
    }
    if (!current) return
    const i = ORDER.findIndex((c) => c.id === current.id)
    if (e.key === 'ArrowRight' && i < ORDER.length - 1) goChart(ORDER[i + 1].id)
    if (e.key === 'ArrowLeft' && i > 0) goChart(ORDER[i - 1].id)
  }

  return (
    <dialog
      ref={dialog}
      onClose={handleDialogClose}
      onClick={closeOnBackdrop(onClose)}
      onKeyDown={handleKeyDown}
      aria-labelledby="map-title"
      className="m-auto p-0 bg-transparent max-w-[min(76rem,96vw)] w-full h-[min(46rem,92vh)]"
    >
      <div
        className="relative h-full flex flex-col rounded-[var(--radius-lg)] bg-[var(--surface)]
          border border-[var(--border)] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center gap-3 px-4 py-2.5 border-b border-[var(--border)] shrink-0">
          {current || showManhaj ? (
            <button type="button" onClick={goUp} title={path.length ? 'Up one level' : 'Back to overview'} aria-label={path.length ? 'Up one level' : 'Back to overview'} className="icon-button">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>
          ) : null}
          <div className="flex-1 min-w-0">
            <h2 id="map-title" className="text-sm font-bold text-[var(--text)] sm:truncate">
              {current ? `${current.en} · ${current.frame}` : showManhaj ? 'Methodologies · المناهج' : 'Map · Nine sciences, one frame per chart'}
            </h2>
            {path.length > 0 && (
              <nav aria-label="Zoom trail" className="flex sm:flex-wrap overflow-x-auto whitespace-nowrap items-center gap-x-1 type-tiny text-[var(--text-faint)]">
                {[tree, ...trail].map((n, depth) => (
                  <span key={depth} className="flex items-center gap-1 min-w-0">
                    {depth > 0 && <span aria-hidden="true">›</span>}
                    {depth === path.length ? (
                      <span aria-current="page" className="text-[var(--text)] truncate">{n.en || n.ar}</span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setPath(path.slice(0, depth))}
                        className="underline decoration-dotted truncate hover:text-[var(--text)]"
                      >
                        {n.en || n.ar}
                      </button>
                    )}
                  </span>
                ))}
              </nav>
            )}
          </div>
          {current && (
            <div className="flex items-center gap-1.5 type-tiny text-[var(--text-faint)]">
              <button type="button" onClick={() => setZoom((z) => Math.max(ZOOM_MIN, z - ZOOM_STEP))} className="icon-button" aria-label="Zoom out">−</button>
              <span className="w-9 text-center">{Math.round(zoom * 100)}%</span>
              <button type="button" onClick={() => setZoom((z) => Math.min(ZOOM_MAX, z + ZOOM_STEP))} className="icon-button" aria-label="Zoom in">+</button>
            </div>
          )}
          <button type="button" onClick={onClose} title="Close (Esc)" aria-label="Close" className="icon-button">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </header>

        <div ref={frame} onTouchEnd={() => setPinching(false)} onTouchCancel={() => setPinching(false)} className="relative flex-1 min-h-0 overflow-auto" tabIndex={0} role="region" aria-label="Map">
          {current ? (
            <div className="p-4" style={{ width: `max(${zoom * 100}%, ${zoom * CHART_MIN_REM}rem)`, transition: pinching ? 'none' : 'width calc(var(--motion-base-ms) * 1ms) ease' }}>
              <PbsChart
                key={path.join('.')}
                config={config}
                activeBranch={hoverBranch}
                onHoverBranch={setHoverBranch}
                onZoom={(rel) => { setPath([...path, ...rel]); setHoverBranch(null) }}
              />
            </div>
          ) : showManhaj ? (
            <ManhajView />
          ) : (
            <MapIndex onOpen={goChart} onOpenManhaj={() => goChart(MANHAJ)} />
          )}

        </div>
      </div>
    </dialog>
  )
}

/** Numbered 1 to 9 by how the sciences lead into each other, in threes that belong together: the law, the sources, the language. The arrow keys walk this same order. */
const ORDER = [...CHARTS].sort((a, b) => a.id.localeCompare(b.id))

/** The nine-card overview: one science per card, click opens its chart; the methodologies card sits apart below.
 * Number, English and frame read down the left, the Arabic name large on the right. */
function MapIndex({ onOpen, onOpenManhaj }) {
  return (
    <div className="p-5 flex flex-col gap-5">
      <div className="grid gap-5 grid-cols-[repeat(auto-fill,minmax(18rem,1fr))]">
        {ORDER.map((chart, delay) => (
          <IndexCard key={chart.id} label={chart.id} ar={chart.ar} en={chart.en} note={chart.frame} color={chart.accent}
            className="pbs-rise border-r-4" style={{ borderRightColor: chart.accent, '--d': `${delay * 55}ms` }}
            onClick={() => onOpen(chart.id)} />
        ))}
      </div>
      <IndexCard label="Beyond the sciences" ar="المناهج والفِرَق"
        en="Methodologies: creed schools, schools of law, Sufi orders, modern movements"
        note="Core beliefs of each, and where they differ"
        className="border-dashed border-[var(--border-hi)]" onClick={onOpenManhaj} />
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
        <span className="block type-small tracking-widest uppercase font-bold tabular-nums text-[var(--text-faint)]">{label}</span>
        <span className="block font-semibold text-[var(--text)]">{en}</span>
        <span className="block type-small text-[var(--text-dim)]">{note}</span>
      </span>
      {/* Takes what the English (min 8rem) leaves: a name too long for that (القواعد الفقهية) breaks
          between its words onto two lines instead of squeezing the English to a word per line. */}
      <ArabicText as="span" size="lg" className="arabic-inline min-w-0 text-right" style={color ? { color } : undefined}>{ar}</ArabicText>
    </button>
  )
}
