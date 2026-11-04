import Mascot from '../display/Mascot'
import { useFirstOfKind } from '../../../lib/motion/useFirstOfKind'

/**
 * Loading placeholder. Size it with Tailwind classes at the call site.
 * `late`: shown only once the wait passes patience-ms (.late), so a quick load goes straight to its answer, no flash.
 * A wrapper, since the shimmer is the skeleton's own animation.
 */
export function Skeleton({ className = '', late = false }) {
  const box = <div className={`skeleton ${className}`} />
  return late ? <div className="late">{box}</div> : box
}

/**
 * The qalam writing: a small pen crossing right to left, the way Arabic is
 * written, leaving a gold line that fades and is written again until the answer
 * comes (styles/components.css .ink-line). Animations off: the line sits still.
 * One pen per screen: a second placeholder waiting at the same time keeps the
 * plain bar it stands in for. The line is that bar's height, so swapping one for
 * the other moves nothing.
 */
function InkLine() {
  const first = useFirstOfKind('ink-line')
  if (!first) return <Skeleton className="h-6 w-1/3" />
  return (
    <div className="ink-line" aria-hidden="true">
      <span className="ink-line-trail" />
      <span className="ink-line-pen"><Mascot mood="thinking" place="ink" /></span>
    </div>
  )
}

/** The shape every panel shows while a request is in flight. */
export function AnalyzerSkeleton() {
  return (
    <div className="space-y-3" aria-hidden="true">
      <InkLine />
      <Skeleton className="h-28 w-full" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  )
}
