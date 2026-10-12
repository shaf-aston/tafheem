/**
 * The way to put the app on a phone's home screen: a slim strip under the
 * header, phones only, shown only when this device can actually do it
 * (lib/install.js decides; this draws). Android gets a button that opens the
 * browser's own install prompt; iPhone has no prompt, so it gets the steps.
 */
import { dismissInstall, install, useInstall } from '../../lib/install'

const SHARE = 'M12 3v12M8 7l4-4 4 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7'

function ShareIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="inline align-[-3px]">
      <path d={SHARE} />
    </svg>
  )
}

export default function InstallBanner() {
  const { kind, dismissed } = useInstall()
  if (dismissed || kind === 'none') return null
  return (
    <div className="shell sm:hidden pt-2">
      <div className="flex items-center gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] px-3 py-2 type-small">
        <span className="flex-1 min-w-0">
          {kind === 'prompt' && 'Add Tafheem to your home screen: opens full screen, like an app.'}
          {kind === 'ios' && (
            <>To install: tap <ShareIcon /> <b>Share</b>, then <b>Add to Home Screen</b>.</>
          )}
          {kind === 'ios-other' && 'To install, open this page in Safari, then Share → Add to Home Screen.'}
        </span>
        {kind === 'prompt' && (
          <button type="button" onClick={install} className="tap shrink-0 rounded-[var(--radius-md)] px-3 py-1 font-semibold bg-[var(--c)] text-[var(--bg)]">
            Install
          </button>
        )}
        <button type="button" onClick={dismissInstall} aria-label="Not now" className="tap shrink-0 px-1 text-[var(--text-dim)]">
          ✕
        </button>
      </div>
    </div>
  )
}
