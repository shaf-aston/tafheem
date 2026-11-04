/**
 * Whether, and how, this device can put the app on its home screen.
 *
 * Four answers, decided here and nowhere else:
 *  - 'prompt'  Android Chrome and friends: the browser hands over an install
 *              prompt (beforeinstallprompt); a button shows it.
 *  - 'ios'     iPhone and iPad have no prompt at all: the only way is Share →
 *              Add to Home Screen, so the user is told the steps.
 *  - 'menu'    Chrome on Android that has not (yet) offered a prompt: its menu has Install app.
 *  - 'android-other'  another Android browser (Firefox, Opera, Brave…): told to open Chrome.
 *  - 'none'    already installed, or a laptop or desktop (never offered: the app
 *              is for the phone).
 * The header's icon (components/shell/InstallButton.jsx) is there whenever the answer is not 'none'; the strip under the
 * header (components/shell/InstallBanner.jsx) opens by itself for every answer but 'menu', and when the icon asks for the steps.
 * What draws them only draws the answer and decides nothing.
 */
import { useSyncExternalStore } from 'react'

import { DEVICE_KEYS, readDevice, writeDevice } from '../store/stored'

const DISMISSED = DEVICE_KEYS.installDismissed

/** iPhone, iPad (which says Mac, with a touchscreen) and iPod. */
export const isIos = (ua, touchPoints = 0) =>
  /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && touchPoints > 1)

/** Chrome on iOS, Firefox on iOS and the like cannot add to the home screen: only Safari can. */
const isIosSafari = (ua) => !/CriOS|FxiOS|EdgiOS|OPiOS|GSA|FBAN|FBAV|Instagram/.test(ua)

/** A phone: Android's own word for it, or an iPhone. Tablets count; a laptop does not. */
/** Plain Chrome on Android, the browser that gives the one-tap prompt. */
const isAndroidChrome = (ua, brave) =>
  / Chrome\//.test(ua) && !/SamsungBrowser|OPR|EdgA|Firefox|YaBrowser|UCBrowser|wv\)/.test(ua) && !brave

const isPhone = (ua, touchPoints = 0) => /Android/.test(ua) || isIos(ua, touchPoints)

/** Pure: the answer for what the page knows. */
export function installKind({ ua = '', touchPoints = 0, standalone = false, prompt = null, brave = false }) {
  if (standalone || !isPhone(ua, touchPoints)) return 'none'
  if (prompt) return 'prompt'
  if (isIos(ua, touchPoints)) return isIosSafari(ua) ? 'ios' : 'ios-other'
  return isAndroidChrome(ua, brave) ? 'menu' : 'android-other'
}

/** Pure: whether the strip under the header is open. It opens by itself unless closed on this device, but a kind whose only advice is "use your menu" waits to be asked. */
export const stripOpen = ({ kind, dismissed, asked }) =>
  kind !== 'none' && (asked || (!dismissed && kind !== 'menu'))

let prompt = null
let installed = false
let asked = false // the icon was pressed and there is no browser prompt to show: the steps are wanted
const listeners = new Set()
const tell = () => listeners.forEach((listener) => listener())

const standalone = () =>
  globalThis.matchMedia?.('(display-mode: standalone)').matches || globalThis.navigator?.standalone === true

/** Start listening, once, at page start: the browser fires beforeinstallprompt early and only once. */
export function watchInstall() {
  globalThis.addEventListener?.('beforeinstallprompt', (event) => {
    event.preventDefault()
    prompt = event
    tell()
  })
  globalThis.addEventListener?.('appinstalled', () => {
    installed = true
    prompt = null
    tell()
  })
}

function kind() {
  const next = installed
    ? 'none'
    : installKind({
        ua: globalThis.navigator?.userAgent ?? '',
        touchPoints: globalThis.navigator?.maxTouchPoints ?? 0,
        standalone: standalone(),
        prompt,
        brave: Boolean(globalThis.navigator?.brave),
      })
  return next
}

const subscribe = (listener) => {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

/** Show the browser's own install prompt. Resolves true if the person accepted. */
export async function install() {
  if (!prompt) return false
  prompt.prompt()
  const { outcome } = await prompt.userChoice
  prompt = null
  tell()
  return outcome === 'accepted'
}

export const dismissInstall = () => {
  asked = false
  writeDevice(DISMISSED, '1')
  tell()
}

/** The header icon pressed: the browser's prompt where it has one, else the steps. */
export function pressInstall() {
  if (prompt) return install()
  asked = true
  tell()
  return Promise.resolve(false)
}

// On this device, not on the shelf: asking again on a new phone is right.
const dismissed = () => readDevice(DISMISSED) === '1'

/** { kind, dismissed, asked } for what draws it; kind is 'prompt' | 'ios' | 'ios-other' | 'menu' | 'android-other' | 'none'. */
export function useInstall() {
  const now = useSyncExternalStore(subscribe, kind)
  const hidden = useSyncExternalStore(subscribe, dismissed)
  const wanted = useSyncExternalStore(subscribe, () => asked)
  return { kind: now, dismissed: hidden, asked: wanted }
}
