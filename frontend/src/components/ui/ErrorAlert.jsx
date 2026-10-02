/**
 * Failure banner. role="alert" so it is announced the moment it appears.
 *
 * `inline` puts the title and the reason on one line, title left, reason
 * right (stacked left on a phone, where right-aligned wrapping read as stray), for a failure inside a section rather than across a page: the
 * stacked shape stood as tall as the diagram it was standing in for.
 *
 * `error` + `fallback` print the reason, `onRetry` the way forward, so the
 * failure-reason-retry trio is written here once instead of on every page.
 * `children` add anything page-specific after the reason.
 */
import { smartError } from '../../lib/apiError'
import RetryButton from './RetryButton'

export default function ErrorAlert({ title, error, fallback, onRetry, children, inline = false }) {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`rise-in rounded-[var(--radius-md)] text-sm border border-[var(--danger-edge)] bg-[var(--danger-wash)] text-[var(--danger)] ${
        inline ? 'px-4 py-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1' : 'p-4 space-y-2'
      }`}
    >
      {title && <div className="font-semibold">{title}</div>}
      <div className={`text-[var(--text-dim)] ${inline ? 'flex flex-col sm:items-end sm:text-right' : ''}`}>
        {error !== undefined && smartError(error, fallback)}
        {children}
        {onRetry && <div><RetryButton onClick={onRetry} /></div>}
      </div>
    </div>
  )
}
