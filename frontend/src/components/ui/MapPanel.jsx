/**
 * The Map: a high-level overview of the nine Islamic sciences as
 * product-breakdown trees, opened from the header like Settings — not a tab,
 * so it never lives in the tab strip or the URL.
 *
 * Two views inside one dialog: an index of nine cards, and a chart view (one
 * science's tree, from PbsChart). A box with deeper topics zooms: the chart
 * redraws with that box as root, and a breadcrumb walks back up. Content is
 * lib/pbsTree over lib/pbsData; this file only holds which view and which
 * zoom path are showing.
 *
 * A native <dialog> is used for the same reason as SettingsPanel: focus
 * trapping, Esc and the backdrop come free from the browser.
 *
 * What this does NOT do yet, on purpose: nothing here tracks how far a reader
 * has gone through a science; a `progress` prop could later decorate a box in
 * PbsChart without restructuring it.
 */
import { useEffect, useMemo, useRef, useState } from 'react'

import ArabicText from './ArabicText'
import PbsChart from './PbsChart'
import './pbs.css'
import { CHARTS } from '../../lib/pbsData'
import { chartTree, nodeAt, viewConfig } from '../../lib/pbsTree'

const ZOOM_MIN = 0.7
const ZOOM_MAX = 2.2
const ZOOM_STEP = 0.2

export default function MapPanel({ open, onClose }) {
  const dialog = useRef(null)
  const [currentId, setCurrentId] = useState(null)
  const [path, setPath] = useState([]) // child indices from the chart root to the zoomed box
  const [hoverBranch, setHoverBranch] = useState(null)
  const [zoom, setZoom] = useState(1)

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
  }, [open])

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
      onClick={(e) => e.target === dialog.current && dialog.current.close()}
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
          {current ? (
            <button type="button" onClick={goUp} title={path.length ? 'Up one level' : 'Back to overview'} aria-label={path.length ? 'Up one level' : 'Back to overview'} className="icon-button">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>
          ) : null}
          <div className="flex-1 min-w-0">
            <h2 id="map-title" className="text-sm font-bold text-[var(--text)] truncate">
              {current ? `${current.en} · ${current.frame}` : 'Map · Nine sciences, one frame per chart'}
            </h2>
            {path.length > 0 && (
              <nav aria-label="Zoom trail" className="flex flex-wrap items-center gap-x-1 type-tiny text-[var(--text-faint)]">
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
          <button type="button" onClick={() => dialog.current?.close()} title="Close (Esc)" aria-label="Close" className="icon-button">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </header>

        <div className="relative flex-1 min-h-0 overflow-auto">
          {current ? (
            <div className="p-4" style={{ width: `${zoom * 100}%`, transition: 'width .2s ease' }}>
              <PbsChart
                key={path.join('.')}
                config={config}
                activeBranch={hoverBranch}
                onHoverBranch={setHoverBranch}
                onZoom={(rel) => { setPath([...path, ...rel]); setHoverBranch(null) }}
              />
            </div>
          ) : (
            <MapIndex onOpen={goChart} />
          )}

        </div>
      </div>
    </dialog>
  )
}

/** Most-linked sciences sit side by side, in pairs down two columns. The arrow keys walk this same order. */
const LINKED = ['01', '02', '07', '04', '05', '03', '06', '09', '08']
const ORDER = LINKED.map((id) => CHARTS.find((c) => c.id === id))

/** The nine-card overview: one science per card, click opens its chart. */
function MapIndex({ onOpen }) {
  return (
    <div className="p-5 grid gap-3 md:grid-cols-2">
      {ORDER.map((chart, delay) => {
        const fg = `var(--science-${chart.id})`
        return (
          <button
            key={chart.id}
            type="button"
            onClick={() => onOpen(chart.id)}
            className="pbs-card pbs-rise md:last:col-span-2 text-right p-4 rounded-[var(--radius-md)] border border-[var(--border)]
              border-r-4 bg-[var(--surface-hi)]"
            style={{ borderRightColor: fg, '--d': `${delay * 55}ms` }}
          >
            <span className="pbs-ghost" style={{ color: fg }} aria-hidden="true">{chart.id}</span>
            <span className="pbs-go text-[var(--text-faint)]" aria-hidden="true">↗</span>
            <p className="type-tiny tracking-widest font-bold text-[var(--text-faint)] relative">{chart.id}</p>
            <ArabicText as="p" size="lg" className="my-0.5 relative" style={{ color: fg }}>
              {chart.ar}
            </ArabicText>
            <p className="type-small text-[var(--text-dim)] relative">{chart.en}</p>
            <p className="type-tiny text-[var(--text-faint)] mt-1.5 relative">{chart.frame}</p>
          </button>
        )
      })}
    </div>
  )
}
