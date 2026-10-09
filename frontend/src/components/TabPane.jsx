/**
 * One tab's panel as App keeps it: shown, or hidden with everything typed and
 * read still in it (App's Activity). Memo, so the hidden ones are not rendered
 * again on every switch; App hands each one props that only change for it.
 */
import { Suspense, memo, useLayoutEffect, useRef } from 'react'

import { finishEntrances } from '../lib/settle'

export default memo(function TabPane({ tab, handoff, accent, onGo, onVisit, onProgress }) {
  const root = useRef(null)
  // Runs on the first showing and again on every return (a hidden panel's
  // effects are torn down), before the frame is painted: see lib/settle. Once
  // more just before that frame, for what a panel measures before it draws
  // (Grow's vine needs its width): that lands in a second render, still unpainted.
  useLayoutEffect(() => {
    finishEntrances(root.current)
    const again = requestAnimationFrame(() => finishEntrances(root.current))
    return () => cancelAnimationFrame(again)
  }, [])
  const Panel = tab.Component
  return (
    <div ref={root} className={tab.study ? 'study' : undefined}>
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
