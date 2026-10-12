/**
 * One tab's panel as App keeps it: shown, or hidden with everything typed and
 * read still in it (App's Activity). Memo, so the hidden ones are not rendered
 * again on every switch; App hands each one props that only change for it.
 */
import { Suspense, memo } from 'react'

import { AnalyzerSkeleton } from '../ui/Skeleton'

export default memo(function TabPane({ tab, handoff, accent, onGo, onVisit, onProgress }) {
  const Panel = tab.Component
  return (
    <div className={tab.study ? 'study' : undefined}>
      <Suspense fallback={<div className="late p-4"><AnalyzerSkeleton /></div>}>
        <Panel
          accent={accent}
          incoming={handoff?.value ?? null}
          arrival={handoff?.at ?? null}
          onGo={onGo}
          onVisit={onVisit}
          onProgress={onProgress}
        />
      </Suspense>
    </div>
  )
})
