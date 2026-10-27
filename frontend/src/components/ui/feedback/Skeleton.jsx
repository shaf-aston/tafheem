/**
 * Loading placeholder. Size it with Tailwind classes at the call site.
 * `late`: shown only once the wait passes patience-ms (.late), so a quick load goes straight to its answer, no flash.
 * A wrapper, since the shimmer is the skeleton's own animation.
 */
export function Skeleton({ className = '', late = false }) {
  const box = <div className={`skeleton ${className}`} />
  return late ? <div className="late">{box}</div> : box
}

/** The shape every panel shows while a request is in flight. */
export function AnalyzerSkeleton() {
  return (
    <div className="space-y-3" aria-hidden="true">
      <Skeleton className="h-6 w-1/3" />
      <Skeleton className="h-28 w-full" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  )
}
