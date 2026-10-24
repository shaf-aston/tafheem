/**
 * Whether, and how, this device can put the app on its home screen.
 *
 * Three phones, three answers, decided here and nowhere else:
 *  - 'prompt'  Android Chrome and friends: the browser hands over an install
 *              prompt (beforeinstallprompt); a button shows it.
 *  - 'ios'     iPhone and iPad have no prompt at all: the only way is Share →
 *              Add to Home Screen, so the user is told the steps.
 *  - 'none'    already installed, a laptop or desktop (never offered: the app
 *              is for the phone), or a browser that cannot.
 * What shows it (components/shell/InstallBanner.jsx) draws the answer and decides nothing.
 */
import { useSyncExternalStore } from 'react'

import { readDevice, writeDevice } from '../store/stored'

const DISMISSED = 'install-dismissed'

/** iPhone, iPad (which says Mac, with a touchscreen) and iPod. */
export const isIos = (ua, touchPoints = 0) =>
  /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && touchPoints > 1)

/** Chrome on iOS, Firefox on iOS and the like cannot add to the home screen: only Safari can. */
const isIosSafari = (ua) => !/CriOS|FxiOS|EdgiOS|OPiOS|GSA|FBAN|FBAV|Instagram/.test(ua)

/** A phone: Android's own word for it, or an iPhone. Tablets count; a laptop does not. */
const isPhone = (ua, touchPoints = 0) => /Android/.test(ua) || isIos(ua, touchPoints)

/** Pure: the answer for what the page knows. */
export function installKind({ ua = '', touchPoints = 0, standalone = false, prompt = null }) {
  if (standalone || !isPhone(ua, touchPoints)) return 'none'
  if (prompt) return 'prompt'
  if (isIos(ua, touchPoints)) return isIosSafari(ua) ? 'ios' : 'ios-other'
  return 'none'
}

let prompt = null
let installed = false
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
  writeDevice(DISMISSED, '1')
  tell()
}

// On this device, not on the shelf: asking again on a new phone is right.
const dismissed = () => readDevice(DISMISSED) === '1'

/** { kind, dismissed } for the banner; kind is 'prompt' | 'ios' | 'ios-other' | 'none'. */
export function useInstall() {
  const now = useSyncExternalStore(subscribe, kind)
  const hidden = useSyncExternalStore(subscribe, dismissed)
  return { kind: now, dismissed: hidden }
}
