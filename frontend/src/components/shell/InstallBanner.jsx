/**
 * The way to put the app on a phone's home screen: a slim strip under the
 * header, phones only, shown only when this device can actually do it
 * (lib/shell/install.js decides, when it opens; this draws). Android gets a button that opens the
 * browser's own install prompt; iPhone has no prompt, so it gets the steps.
 * Closing it hides only the strip: the header's icon (InstallButton) opens it again, and Settings keeps the same steps (InstallPanel).
 */
import { dismissInstall, install, stripOpen, useInstall } from '../../lib/shell/install'

const SHARE = 'M12 3v12M8 7l4-4 4 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7'

function ShareIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="inline align-[-3px]">
      <path d={SHARE} />
    </svg>
  )
}

/**
 * What this device is told and offered, for a kind other than 'none'. The banner
 * and Settings both draw this, so the words and the button cannot drift apart.
 */
export function InstallSteps({ kind }) {
  return (
    <>
      <span className="flex-1 min-w-0">
        {kind === 'prompt' && 'Add Tafheem to your home screen: opens full screen, like an app.'}
        {kind === 'ios' && (
          <>To install: tap <ShareIcon /> <b>Share</b>, then <b>Add to Home Screen</b>.</>
        )}
        {kind === 'ios-other' && 'To install, open this page in Safari, then Share → Add to Home Screen.'}
        {kind === 'menu' && 'To install, open your browser’s menu (⋮), then tap Install app or Add to Home screen.'}
      </span>
      {kind === 'prompt' && (
        <button type="button" onClick={install} className="tap shrink-0 rounded-[var(--radius-md)] px-3 py-1 font-semibold bg-[var(--c,var(--primary))] text-[var(--bg)]">
          Install
        </button>
      )}
    </>
  )
}

export default function InstallBanner() {
  const state = useInstall()
  const { kind } = state
  if (!stripOpen(state)) return null
  return (
    <div className="shell sm:hidden pt-2">
      <div className="flex items-center gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] px-3 py-2 type-small">
        <InstallSteps kind={kind} />
        <button type="button" onClick={dismissInstall} aria-label="Not now" className="tap shrink-0 px-1 text-[var(--text-dim)]">
          ✕
        </button>
      </div>
    </div>
  )
}
