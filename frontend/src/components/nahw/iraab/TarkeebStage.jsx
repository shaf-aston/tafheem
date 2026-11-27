/**
 * The analysed sentence's tarkeeb, laid out for the screen it is on.
 *
 * Wide (a computer, a phone turned sideways): the packed book chart, whole and fitted
 * to the width, with the tapped word answered in a panel beside it, so nothing covers
 * the chart. A phone held upright: the same tree as a list, read downwards, each word's
 * answer opening under its own line; "Chart" shows the drawing too. "Full screen" fills
 * the screen with the chart and turns a phone sideways where the browser lets it.
 */
import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'

import { align, layout } from '../../../lib/nahw/tarkeebLayout'
import { useMedia } from '../../../lib/hooks/useMedia'
import TarkeebCompact from '../../grammar/tarkeeb/TarkeebCompact'
import TarkeebOutline from '../../grammar/tarkeeb/TarkeebOutline'
import Segmented from '../../ui/inputs/Segmented'
import WordDetail from '../WordDetail'

const UPRIGHT_PHONE = '(max-width: 39.99rem) and (orientation: portrait)'
const SIDE_PANEL = '(min-width: 64rem)'
// full screen's zoom steps, as times the size that fits the whole chart
const ZOOMS = [1, 1.5, 2, 3]
const VIEWS = [
  { id: 'list', label: 'List' },
  { id: 'chart', label: 'Chart' },
]

export default function TarkeebStage({ data, kind, glosses, onMore, onLookup, foot }) {
  const upright = useMedia(UPRIGHT_PHONE)
  const side = useMedia(SIDE_PANEL)
  const [phoneView, setPhoneView] = useState('list')
  // the tapped word, kept with the sentence it was tapped in, so a new sentence starts with none
  const [picked, setPick] = useState(null)
  const pick = picked?.of === data ? picked : null
  const [full, setFull] = useState(false)
  const [zoom, setZoom] = useState(0)

  // which card and which English each word on the chart is, lined up once per answer (tarkeebLayout.align)
  const onPage = useMemo(() => (data.tree?.tree ? layout(data.tree).written : []), [data.tree])
  const cards = useMemo(() => align(onPage, data.words, 'word', { byPlace: true }), [onPage, data.words])
  const englishes = useMemo(() => align(onPage, glosses, 'arabic'), [onPage, glosses])
  const word = pick && cards[pick.nth]
  const english = pick && englishes[pick.nth]?.english
  const choose = (text, nth) => setPick(pick?.nth === nth ? null : { text, nth, of: data })

  const enterFull = async () => {
    setFull(true)
    setZoom(0)
    try {
      // the page itself, asked inside the tap (a browser allows it only then); the stage covers it
      await document.documentElement.requestFullscreen?.()
      await screen.orientation?.lock?.('landscape')
    } catch { /* an iPhone, or a browser that will not: the stage still fills the window */ }
  }
  const leaveFull = () => {
    setFull(false)
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
    screen.orientation?.unlock?.()
  }
  useEffect(() => {
    const left = () => { if (!document.fullscreenElement) setFull(false) }
    document.addEventListener('fullscreenchange', left)
    return () => document.removeEventListener('fullscreenchange', left)
  }, [])
  useEffect(() => {
    if (!full) return undefined
    const esc = (e) => { if (e.key === 'Escape') leaveFull() }
    addEventListener('keydown', esc)
    return () => removeEventListener('keydown', esc)
  }, [full])

  const detail = word && (
    <WordDetail word={word} english={english} onClose={() => setPick(null)}
      onMore={() => onMore(word)} onLookup={() => onLookup?.(pick.text)} />
  )
  const fullButton = (
    <button type="button" onClick={enterFull}
      className="press tap shrink-0 inline-flex items-center gap-1.5 px-3 py-2 type-label rounded-[var(--radius-md)] border border-[var(--border)] text-[var(--text-dim)]">
      <span aria-hidden="true">⤢</span> Full screen
    </button>
  )
  const chart = <TarkeebCompact tarkeeb={data.tree} picked={pick?.nth} onWord={choose} />

  return (
    <div className="space-y-2">
      <section aria-label="Tarkeeb" className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]">
        <div className="flex flex-wrap items-center justify-between gap-2 px-4 pt-3">
          <h3 className="flex flex-wrap items-center gap-2 type-ui text-[var(--text)]">
            <span className="type-label uppercase tracking-wide text-[var(--text-faint)]">Tarkeeb</span>{kind}
          </h3>
          <div className="flex items-center gap-2">
            {upright && <Segmented compact label="Show the tarkeeb as a list or as the chart" value={phoneView} onChange={setPhoneView} options={VIEWS} />}
            {fullButton}
          </div>
        </div>
        {upright && phoneView === 'list' ? (
          <div className="px-3 pb-3 pt-1">
            <TarkeebOutline tarkeeb={data.tree} picked={pick?.nth} onWord={choose}
              detail={detail && <div className="my-2 tko-detail">{detail}</div>} />
          </div>
        ) : (
          <div className={side ? 'grid grid-cols-[minmax(0,1fr)_16rem] gap-4 px-4 pb-3' : 'px-3 pb-3'}>
            <div className="min-w-0 self-center py-2">{chart}</div>
            {side ? (
              <aside aria-live="polite" className="border-s border-[var(--border)] ps-4 py-3 min-h-[10rem]">
                {detail || <WordDetail.Empty />}
              </aside>
            ) : detail && <div className="mt-2">{detail}</div>}
          </div>
        )}
        {upright && phoneView === 'chart' && (
          <p className="px-4 pb-3 -mt-1 type-small text-[var(--text-faint)]">Small? Tap Full screen, or turn your phone sideways.</p>
        )}
        {foot}
      </section>

      {/* on the page's body: inside the card, its rise-in transform would pin it to the card, not the screen */}
      {full && createPortal(
        <div className="tks-full" role="dialog" aria-label="Tarkeeb, full screen">
          <div className="tks-full-bar">
            <span className="type-label text-[var(--text-faint)] tks-turn min-w-0 truncate">⟳ Turn sideways</span>
            <div role="group" aria-label="Zoom" className="ms-auto shrink-0 flex items-center gap-1">
              <button type="button" className="press tap tks-zoom" aria-label="Zoom out" disabled={zoom === 0}
                onClick={() => setZoom((z) => Math.max(0, z - 1))}>−</button>
              <button type="button" className="press tap tks-zoom tks-zoom-fit" aria-label="Fit the whole chart" aria-pressed={zoom === 0}
                onClick={() => setZoom(0)}>Fit</button>
              <button type="button" className="press tap tks-zoom" aria-label="Zoom in" disabled={zoom === ZOOMS.length - 1}
                onClick={() => setZoom((z) => Math.min(ZOOMS.length - 1, z + 1))}>+</button>
            </div>
            <button type="button" onClick={leaveFull} aria-label="Close full screen"
              className="press tap shrink-0 whitespace-nowrap px-3 py-2 type-label rounded-[var(--radius-md)] border border-[var(--border)] text-[var(--text)]">
              Close ✕
            </button>
          </div>
          <div className="tks-full-chart">
            <TarkeebCompact tarkeeb={data.tree} picked={pick?.nth} onWord={choose} fill zoom={ZOOMS[zoom]} />
          </div>
          {detail && <div className="tks-full-detail">{detail}</div>}
        </div>,
        document.body,
      )}
    </div>
  )
}
