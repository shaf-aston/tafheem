/**
 * The zoom of a chart: − slider + and the percentage, with Fit to draw it back at 100% (the chart fitted to its
 * frame). Drawn the same wherever a chart zooms; lib/hooks/useZoom owns the zoom and `knobs` are config/zoom.json's.
 */
export default function ZoomBar({ zoom, knobs, onStep, onSet, onReset }) {
  const { min, max, step } = knobs
  return (
    <div className="flex items-center gap-1.5 shrink-0" role="group" aria-label="Zoom">
      <button type="button" onClick={() => onStep(-1)} disabled={zoom <= min} className="icon-button" aria-label="Zoom out">−</button>
      <input
        type="range"
        min={min}
        max={max}
        step={step / 5}
        value={zoom}
        onChange={(event) => onSet(Number(event.target.value))}
        aria-label="Zoom level"
        aria-valuetext={`${Math.round(zoom * 100)}%`}
        className="w-20 sm:w-28 accent-[var(--c,var(--text-dim))]"
      />
      <button type="button" onClick={() => onStep(1)} disabled={zoom >= max} className="icon-button" aria-label="Zoom in">+</button>
      <span className="w-11 text-center tabular-nums">{Math.round(zoom * 100)}%</span>
      <button type="button" onClick={onReset} disabled={zoom === 1} className="type-small underline decoration-dotted underline-offset-4 disabled:opacity-40 disabled:no-underline">Fit</button>
    </div>
  )
}
