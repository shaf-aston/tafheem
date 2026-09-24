/** Loading placeholder. Size it with Tailwind classes at the call site. */
export function Skeleton({ className = '' }) {
  return <div className={`skeleton ${className}`} />
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
