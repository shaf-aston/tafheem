/**
 * The one way this app keeps anything in the browser: settings, remembered
 * choices (useRemembered), recent searches (useHistory), best streak, the walked
 * path (session.js).
 *
 * Everything is filed under who is logged in: "@amina/settings" for amina, the
 * bare "settings" for the guest. So two people on one browser never see each
 * other's settings or records, and logging in switches all of it at once with
 * no panel knowing. One account's keys are its shelf, which lib/store/shelf.js copies
 * to the server so the name brings it to any device. The username itself is
 * the device's, not anyone's shelf, so it is read bare (readDevice), and so is the device's guest id
 * (lib/learner/profile.js deviceId): neither is ever wiped by Start over or copied into an account.
 *
 * Quiz answers are rows in a database on the machine, not in the browser, so
 * they go through lib/learner/progress.js first; "clear it all" has to mean Review
 * as well, or the button says more than it does.
 */
import { useCallback, useMemo, useSyncExternalStore } from 'react'

import PROFILE from '../../config/profile.json'
import { forgetProgress } from '../learner/progress'

// Usernames never hold "@" (services/learner/username.py), and no bare key starts with it.
const MARK = '@'

/** The store itself, or null where there is none or it throws on touch. */
function store() {
  try {
    return globalThis.localStorage ?? null
  } catch {
    return null
  }
}

/** A key as the device holds it: the bare key, before any name is put on it. */
export function readDevice(key, fallback = '') {
  try {
    return store()?.getItem(key) ?? fallback
  } catch {
    return fallback
  }
}

export function writeDevice(key, text) {
  try {
    store()?.setItem(key, text)
  } catch {
    /* private browsing, the value still holds for this visit */
  }
}

export function forgetDevice(key) {
  try {
    store()?.removeItem(key)
  } catch {
    /* nothing stored to remove */
  }
}

/** Who is logged in on this device, '' for the guest. */
const owner = () => readDevice(PROFILE.storageKey)

/** Where a key is filed for `name`. */
const filed = (key, name = owner()) => (name ? `${MARK}${name}/${key}` : key)

/** Every key `name` has, bare. The guest's are the bare keys other than the username and the device's id. */
function ownKeys(name = owner()) {
  try {
    const all = Array.from({ length: store()?.length ?? 0 }, (_, index) => store().key(index))
    if (name) {
      const head = filed('', name)
      return all.filter((key) => key?.startsWith(head)).map((key) => key.slice(head.length))
    }
    return all.filter((key) => key && !key.startsWith(MARK) && key !== PROFILE.storageKey && key !== PROFILE.deviceKey)
  } catch {
    return []
  }
}

// Told after every write or forget, so lib/store/shelf.js can send the shelf up.
const listeners = new Set()
const changed = () => listeners.forEach((listener) => listener())

/** Hear every change to the logged-in shelf. Returns the way to stop. */
export function onChange(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

/** One account's whole shelf: bare key -> stored text. */
export function shelfOf(name = owner()) {
  return Object.fromEntries(ownKeys(name).map((key) => [key, readDevice(filed(key, name))]))
}

// Told when the whole shelf is swapped from outside (the server's copy landed).
// Kept apart from `listeners`: that copy came from the server, so it is not sent back.
const replacedListeners = new Set()

/** Hear the whole shelf being replaced. Returns the way to stop. */
export function onReplaced(listener) {
  replacedListeners.add(listener)
  return () => replacedListeners.delete(listener)
}

/** Replace one account's shelf with `data`, as lib/store/shelf.js got it from the server. */
export function fillShelf(name, data) {
  ownKeys(name).forEach((key) => forgetDevice(filed(key, name)))
  Object.entries(data).forEach(([key, text]) => writeDevice(filed(key, name), text))
  replacedListeners.forEach((listener) => listener())
}

/**
 * The one way a component reads the store: live. The page never waits for the
 * server's shelf before showing; it shows this device's copy, and when the
 * server's lands every reader picks it up here, with no panel knowing.
 */
const subscribe = (notify) => {
  const stops = [onChange(notify), onReplaced(notify)]
  return () => stops.forEach((stop) => stop())
}

/** The stored string, kept live. */
export const useStoredRaw = (key) => useSyncExternalStore(subscribe, () => readRaw(key))

/** The stored JSON value, kept live; the fallback as readSaved gives it. */
export function useStoredSaved(key, fallback) {
  const text = useStoredRaw(key)
  // eslint-disable-next-line react-hooks/exhaustive-deps -- parsed once per stored text
  return useMemo(() => readSaved(key, fallback), [key, text])
}

/** Like useState, but the value lives in the store: [value, set], set taking a value or an updater. */
export function useSavedState(key, fallback) {
  const value = useStoredSaved(key, fallback)
  const set = useCallback((next) => {
    writeSaved(key, typeof next === 'function' ? next(readSaved(key, fallback)) : next)
  // eslint-disable-next-line react-hooks/exhaustive-deps -- the fallback is a literal at each call site
  }, [key])
  return [value, set]
}

// Every browser-store read and write in lib/ goes through these. Storage can
// throw (private browsing, quota), so none of them ever does.

/** The stored string as written, or the fallback when missing or storage throws. */
export function readRaw(key, fallback = '') {
  return readDevice(filed(key), fallback)
}

/** Store a string as is; in private browsing it is silently kept for this visit only. */
export function writeRaw(key, text) {
  writeDevice(filed(key), text)
  changed()
}

/** The stored JSON value, or the fallback when missing, unparseable or storage throws. */
export function readSaved(key, fallback) {
  const text = readDevice(filed(key), null)
  try {
    return text == null ? fallback : JSON.parse(text)
  } catch {
    return fallback
  }
}

/** Store a value as JSON, same private-browsing rule as writeRaw. */
export function writeSaved(key, value) {
  writeRaw(key, JSON.stringify(value))
}

/**
 * The learner's own record (Grow steps, Tamreen answers, best streak) is kept
 * under this prefix, so Start over forgets all of it by one rule: a new module's
 * record is covered the day it is named through progressKey, with no list to update.
 */
const PROGRESS = 'progress:'
export const progressKey = (name) => `${PROGRESS}${name}`

/** Forget every record kept under progressKey; choices and settings stay. */
export function forgetProgressKeys() {
  ownKeys().filter((key) => key.startsWith(PROGRESS)).forEach((key) => forgetDevice(filed(key)))
  changed()
}

/** Forget one key. */
export function forgetKey(key) {
  forgetDevice(filed(key))
  changed()
}

/**
 * Forget it all for whoever is logged in, then reload. Other accounts on this
 * browser keep theirs, and the login stays: this is starting over, not leaving.
 *
 * The reload is required, not tidiness: settings and remembered choices are
 * also held in React state, so clearing underneath them leaves stale values on
 * screen and the next click writes one straight back.
 */
export async function forgetSaved() {
  ownKeys().forEach((key) => forgetDevice(filed(key)))
  changed() // the empty shelf goes up too, if a push was already waiting
  await forgetProgress()
  globalThis.location?.reload()
}
