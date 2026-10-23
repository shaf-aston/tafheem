/**
 * One tab's panel as App keeps it: shown, or hidden with everything typed and
 * read still in it (App's Activity). Memo, so the hidden ones are not rendered
 * again on every switch; App hands each one props that only change for it.
 *
 * The page's fade-in is worn here, once, for every tab: it used to sit on
 * SectionHeader, so only a title faded and the rest of the page snapped in,
 * and a screen with no header (Grow's lessons) did not fade at all. A hidden
 * pane is display:none, so showing it again replays the fade.
 */
import { Suspense, memo } from 'react'

import { AnalyzerSkeleton } from '../ui/Skeleton'

export default memo(function TabPane({ tab, handoff, accent, onGo, onVisit, onProgress }) {
  const Panel = tab.Component
  return (
    <div className={tab.study ? 'study fade-in' : 'fade-in'}>
      <Suspense fallback={<div className="late p-4"><AnalyzerSkeleton /></div>}>
        <Panel
          accent={accent}
          incoming={handoff?.value ?? null}
          arrival={handoff?.at ?? null}
          handed={handoff?.handed ?? false}
          onGo={onGo}
          onVisit={onVisit}
          onProgress={onProgress}
        />
      </Suspense>
    </div>
  )
})
