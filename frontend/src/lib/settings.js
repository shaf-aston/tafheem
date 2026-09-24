/**
 * The only module that reads settings.json.
 *
 * Mirrors theme.js: config in one file, one reader, components ask this module.
 * The difference is that a theme token is fixed at build time and a setting is
 * the reader's own choice, kept in localStorage and re-applied on every load.
 *
 * A setting reaches the screen one of two ways, and never a third:
 *   • it writes a CSS custom property on :root, which the stylesheet already
 *     reads (this is why nothing here knows about any component), or
 *   • a component asks for it by name with useSetting().
 *
 * Two kinds exist: a 'choice' picks one of its listed options, a 'switch' is on
 * or off. Both are stored by name, so a stored value stays readable and an
 * option that later disappears falls back to the default instead of breaking.
 */
import { useSyncExternalStore } from 'react'

import config from '../settings.json'
import { themeVariable } from '../theme'

/** Every setting, in the order the panel shows them. */
export const SETTINGS = config.settings

const STORAGE_KEY = config['storage-key']
const BY_KEY = Object.fromEntries(SETTINGS.map((one) => [one.key, one]))
const listeners = new Set()

/** The root element, or null when there is no DOM (tests run without one). */
const rootElement = () => globalThis.document?.documentElement ?? null

// A stored value is untrusted: it survives config changes, and a person can
// edit it by hand. Anything out of range or of the wrong type falls back to the
// default rather than reaching the screen.
function clean(setting, value) {
  if (setting.type === 'switch') return typeof value === 'boolean' ? value : setting.default
  return setting.options.some((one) => one.id === value) ? value : setting.default
}

/** What a setting puts in its CSS variable, or null if it drives no CSS. */
function cssValue(setting, value) {
  if (!setting.css) return null
  return String(setting.options.find((one) => one.id === value).write)
}

function saved() {
  try {
    return JSON.parse(globalThis.localStorage?.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {} // unreadable or private browsing, the defaults still work
  }
}

// Read once, then keep the answer: useSyncExternalStore compares snapshots by
// identity, so re-parsing storage on every render would loop forever.
let current = null

function values() {
  if (!current) {
    const stored = saved()
    current = Object.fromEntries(
      SETTINGS.map((one) => [one.key, one.key in stored ? clean(one, stored[one.key]) : one.default]),
    )
  }
  return current
}

/** Write every setting onto :root. Called at startup and after each change. */
export function applySettings(root = rootElement()) {
  if (!root) return
  const chosen = values()
  for (const setting of SETTINGS) {
    const value = chosen[setting.key]
    const css = cssValue(setting, value)
    if (css !== null) root.style.setProperty(setting.css, css)
    // A switch only overrides while it is off; on means "whatever the theme
    // says". That has to be written back, not removed: theme.js writes to this
    // same :root, so removing the property deletes the theme's own value and
    // leaves every rule reading it with nothing, which is how the motion
    // durations came out empty and silently killed the animations they timed.
    for (const [name, off] of Object.entries(setting.off ?? {})) {
      if (!value) {
        root.style.setProperty(name, String(off))
        continue
      }
      const base = themeVariable(name)
      if (base === undefined) root.style.removeProperty(name)
      else root.style.setProperty(name, base)
    }
  }
}

/** Change one setting. Unknown keys are ignored rather than stored as junk. */
export function setSetting(key, value) {
  const setting = BY_KEY[key]
  if (!setting) return
  current = { ...values(), [key]: clean(setting, value) }
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, JSON.stringify(current))
  } catch {
    /* private browsing, the choice still holds for this session */
  }
  applySettings()
  for (const listener of listeners) listener()
}

/** Put everything back to the defaults in settings.json. */
export function resetSettings() {
  current = Object.fromEntries(SETTINGS.map((one) => [one.key, one.default]))
  try {
    globalThis.localStorage?.removeItem(STORAGE_KEY)
  } catch {
    /* nothing stored to remove */
  }
  applySettings()
  for (const listener of listeners) listener()
}

/** One setting's current value, kept in step across every component showing it. */
export function useSetting(key) {
  return useSyncExternalStore(
    (notify) => {
      listeners.add(notify)
      return () => listeners.delete(notify)
    },
    () => values()[key],
    () => BY_KEY[key]?.default,
  )
}
