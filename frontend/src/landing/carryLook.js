/**
 * The landing is the dark look. A first visit that goes on into the app lands in that same look, not in
 * whatever the device prefers, so "See it in action" opens the page it promised. Only when the app has never
 * been opened here (no hint yet): a look already chosen, or Device already followed, is left alone. The app
 * starts from this hint until the reader picks a look in Settings (lib/store/settings.js), and the boot script
 * paints its ground from the first frame (vite/bootShell.js).
 */
import theme from '../config/theme.json'
import { DEVICE_KEYS, readDevice, writeDevice } from '../lib/store/device'

/** Called with the link a click landed on (or null); `here` is the page's own address. */
export function carryLook(link, here = globalThis.location) {
  if (!link || new URL(link.href, here.href).origin !== here.origin || link.pathname === here.pathname) return
  if (!readDevice(DEVICE_KEYS.themeHint, '')) writeDevice(DEVICE_KEYS.themeHint, theme.themes.base)
}
