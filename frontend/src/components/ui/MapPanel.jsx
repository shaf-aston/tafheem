/**
 * The Map: a high-level overview of the nine Islamic sciences as
 * product-breakdown trees, opened from the header like Settings — not a tab,
 * so it never lives in the tab strip or the URL.
 *
 * Two views inside one dialog: an index of nine cards, and a chart view (one
 * science's tree, from PbsChart, with a side detail panel from PbsDetail on
 * click). Content is lib/pbsData, unchanged; this file only holds the small
 * amount of state that decides which view and which node are showing.
 *
 * A native <dialog> is used for the same reason as SettingsPanel: focus
 * trapping, Esc and the backdrop come free from the browser.
 *
 * What this does NOT do yet, on purpose: nothing here tracks how far a reader
 * has gone through a science. That's the next layer, once this overview
 * itself is in place — a `progress` prop could later decorate a kid's box in
 * PbsChart / a line in PbsDetail without restructuring either.
 */
import { useEffect, useRef, useState } from 'react'

import ArabicText from './ArabicText'
import PbsChart from './PbsChart'
import PbsDetail from './PbsDetail'
import './pbs.css'
import { CHARTS } from '../../lib/pbsData'

const ZOOM_MIN = 0.7
const ZOOM_MAX = 2.2
const ZOOM_STEP = 0.2

export default function MapPanel({ open, onClose }) {
  const dialog = useRef(null)
  const [currentId, setCurrentId] = useState(null)
  const [pinnedBranch, setPinnedBranch] = useState(null)
  const [hoverBranch, setHoverBranch] = useState(null)
  const [detail, setDetail] = useState(null) // { branchIndex, kidIndex? }
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
    setPinnedBranch(null)
    setHoverBranch(null)
    setDetail(null)
    setZoom(1)
    onClose()
  }

  const current = CHARTS.find((c) => c.id === currentId) ?? null

  const goIndex = () => { setCurrentId(null); setPinnedBranch(null); setHoverBranch(null); setDetail(null) }
  const goChart = (id) => { setCurrentId(id); setPinnedBranch(null); setHoverBranch(null); setDetail(null) }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      if (detail) { e.preventDefault(); setDetail(null); return }
      if (current) { e.preventDefault(); goIndex(); return }
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
            <button type="button" onClick={goIndex} title="Back to overview" aria-label="Back to overview" className="icon-button">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>
          ) : null}
          <h2 id="map-title" className="text-sm font-bold text-[var(--text)] flex-1 min-w-0 truncate">
            {current ? `${current.en} · ${current.frame}` : 'Map · Nine sciences, one frame per chart'}
          </h2>
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
                config={current.config}
                activeBranch={hoverBranch ?? pinnedBranch}
                onHoverBranch={setHoverBranch}
                onSelectBranch={(i) => { setPinnedBranch(i); setDetail({ branchIndex: i, kidIndex: null }) }}
                onSelectKid={(bi, ki) => { setPinnedBranch(bi); setDetail({ branchIndex: bi, kidIndex: ki }) }}
              />
            </div>
          ) : (
            <MapIndex onOpen={goChart} />
          )}

          {current && detail && (
            <PbsDetail
              chart={current}
              branchIndex={detail.branchIndex}
              kidIndex={detail.kidIndex}
              onSelectKid={(bi, ki) => { setPinnedBranch(bi); setDetail({ branchIndex: bi, kidIndex: ki }) }}
              onClose={() => setDetail(null)}
            />
          )}
        </div>
      </div>
    </dialog>
  )
}

/** The charts as the board shows them: by group, then by id. The arrow keys walk this same order. */
const GROUPS = []
for (const chart of CHARTS) {
  let g = GROUPS.find((x) => x.name === chart.group)
  if (!g) { g = { name: chart.group, items: [] }; GROUPS.push(g) }
  g.items.push(chart)
}
for (const g of GROUPS) g.items.sort((a, b) => a.id.localeCompare(b.id))
const ORDER = GROUPS.flatMap((g) => g.items)

/** The nine-card overview: one science per card, click opens its chart. */
function MapIndex({ onOpen }) {

  // A running index across every card, groups included, so the stagger reads
  // top to bottom the way the eye does, not restarting at each group.
  let seen = 0

  return (
    <div className="p-5 max-w-[64rem]">
      <p className="type-small text-[var(--text-dim)] max-w-[42rem] mb-6">
        One rule across all nine: every level-2 node is a book-level division of its own science,
        never a باب lifted from elsewhere. Click a science to see its tree, then any node for what
        sits inside it.
      </p>
      {GROUPS.map((g) => (
        <section key={g.name} className="mb-7">
          <h3 className="type-tiny tracking-widest font-bold text-[var(--text-faint)] uppercase mb-2.5">
            {g.name}
          </h3>
          <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(14rem, 1fr))' }}>
            {g.items.map((chart) => {
              const delay = seen++
              const fg = `var(--science-${chart.id})`
              return (
                <button
                  key={chart.id}
                  type="button"
                  onClick={() => onOpen(chart.id)}
                  className="pbs-card pbs-rise text-right p-4 rounded-[var(--radius-md)] border border-[var(--border)]
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
        </section>
      ))}
    </div>
  )
}
