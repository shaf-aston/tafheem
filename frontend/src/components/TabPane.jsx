/**
 * One tab's panel as App keeps it: shown, or hidden with everything typed and
 * read still in it (App's Activity). Memo, so the hidden ones are not rendered
 * again on every switch; App hands each one props that only change for it.
 */
import { Suspense, memo } from 'react'

import { useSettled } from '../lib/settle'

export default memo(function TabPane({ tab, handoff, accent, onGo, onVisit, onProgress }) {
  // Arriving on the first showing and again on every return, a hidden panel's
  // effects being torn down: its data landing after a reload arrives finished too (lib/settle).
  useSettled()
  const Panel = tab.Component
  return (
    <div className={tab.study ? 'study' : undefined}>
      <Suspense fallback={null}>
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
