/**
 * The header's way to put the app on a phone, always there while it can be done
 * (lib/shell/install.js decides; this draws). Android with a browser prompt: one
 * tap opens it. Anywhere else the same tap opens the steps in the strip under the header (InstallBanner).
 * Phones only: a laptop, or an app already on the home screen, shows nothing.
 */
import { useMedia, PHONE } from '../../lib/hooks/useMedia'
import { pressInstall, useInstall } from '../../lib/shell/install'

const DOWNLOAD = ['M12 3v12', 'M7 11l5 5 5-5', 'M5 21h14']

export default function InstallButton() {
  const { kind } = useInstall()
  const phone = useMedia(PHONE)
  if (!phone || kind === 'none') return null
  return (
    <button type="button" onClick={pressInstall} title="Install on your phone" aria-label="Install Tafheem on your phone" className="icon-button">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {DOWNLOAD.map((d) => <path key={d} d={d} />)}
      </svg>
    </button>
  )
}
