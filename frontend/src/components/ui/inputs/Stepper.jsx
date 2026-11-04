/**
 * Back and on one: a surah, an ayah. The same two round arrows wherever
 * something is stepped through, so a header and a sheet cannot draw them twice.
 * Either handler null means there is nothing that way, and the arrow is off.
 * `label` is the thing stepped ("surah"), said to a screen reader.
 */
export default function Stepper({ label, onPrev, onNext }) {
  const arrow = `press tap grid place-items-center w-[var(--layout-chip)] h-[var(--layout-chip)] shrink-0
    rounded-full border border-[var(--border)] text-[var(--text-dim)] transition-colors
    hover:text-[var(--text)] hover:border-[var(--c,var(--border-hi))]
    disabled:opacity-30 disabled:hover:border-[var(--border)]`
  return (
    <div className="flex items-center gap-2">
      <button type="button" className={arrow} onClick={onPrev} disabled={!onPrev} aria-label={`Previous ${label}`}>‹</button>
      <button type="button" className={arrow} onClick={onNext} disabled={!onNext} aria-label={`Next ${label}`}>›</button>
    </div>
  )
}
