import { useState } from 'react'

import ErrorAlert from '../ui/ErrorAlert'
import { copy, noSignal } from '../../lib/offline'

// Telling a visitor to start a server on their own machine only makes sense on
// the machine the server would run on.
const OWN_MACHINE = ['localhost', '127.0.0.1'].includes(window.location.hostname)

/** Under the header while the backend cannot be reached, until dismissed. */
export default function BackendBanner({ status }) {
  const [dismissed, setDismissed] = useState(false)
  // Dismissing hides this outage only. Once the backend is back, the next drop
  // is news again; before this, one click silenced every later outage too.
  // Set while drawing rather than in an effect: React redraws at once, with no
  // frame showing the old outage's dismissal.
  if (status === 'ok' && dismissed) setDismissed(false)
  if (status !== 'error' || dismissed) return null
  return (
    <div className="shell pt-4 relative">
      <ErrorAlert title={noSignal() ? copy['offline-title'] : OWN_MACHINE ? 'Backend offline' : 'Not connected yet'}>
        {noSignal() ? copy['offline-body'] : OWN_MACHINE ? (
          <>
            The backend is not running.
            {/* The command was the only advice here; most readers can't run
                it, so it moves behind a summary instead of leading. */}
            <details className="mt-2">
              <summary className="cursor-pointer">The command, if you run it yourself</summary>
              <code className="mt-1 block px-1 rounded bg-[var(--surface-hi)] text-[var(--text)]">
                python -m uvicorn backend.main:app --reload
              </code>
            </details>
          </>
        ) : (
          <>
            The books this reads from are not attached to this copy yet, so nothing here
            will load. <a className="underline" href="/">The front page</a> shows what it does.
          </>
        )}
      </ErrorAlert>
      <button
        type="button"
        aria-label="Dismiss backend warning"
        onClick={() => setDismissed(true)}
        className="absolute top-4 right-4 min-w-[calc(var(--layout-tap-min)*1px)] min-h-[calc(var(--layout-tap-min)*1px)] grid place-items-center hover:opacity-70 text-sm"
      >
        {/* The visible disc stays small; the button around it is the finger's target. */}
        <span
          aria-hidden="true"
          className="w-7 h-7 grid place-items-center rounded-full border text-[var(--danger)] bg-[var(--surface)]"
          style={{ borderColor: 'var(--danger-edge)' }}
        >
          ✕
        </span>
      </button>
    </div>
  )
}
