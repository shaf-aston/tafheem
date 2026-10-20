/**
 * The app on this phone with no signal: the worker that saves it, and the packs a reader can add.
 *
 * The rules are src/offline.json; vite/offline.js turns them into the built plan
 * (/offline-files.json), and vite/sw.template.js serves from what is saved. This file starts the
 * worker and keeps the packs: each is its own cache, filled here and read by the worker, so
 * removing one is deleting one cache. What shows it (components/shell/OfflinePanel.jsx) draws and
 * decides nothing.
 */
import { useSyncExternalStore } from 'react'

import knobs from '../offline.json'
import { fill } from './homeCopy'

export const { copy, packs: PACKS } = knobs
const PLAN_URL = '/offline-files.json'
const PACK = 'tafheem-pack-'
const AT_ONCE = 4

/** No signal at all: not the server's fault, and what is saved on the phone still opens. */
export const noSignal = () => globalThis.navigator?.onLine === false

/** "2.5 MB", or "300 KB" under one. */
export function sizeLabel(bytes) {
  const mb = bytes / 1e6
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1e3))} KB`
}

/** Pure: a pack's state from how many of its files are saved. */
export const packState = (have, total) => (total > 0 && have >= total ? 'ready' : 'none')

/** The core-ready line, with the core's size filled in. */
export const coreLine = (bytes) => fill(copy['core-ready'], { size: sizeLabel(bytes) })

const supported = () =>
  import.meta.env.PROD && 'serviceWorker' in (globalThis.navigator ?? {}) && 'caches' in globalThis

let state = { supported: false, core: 'saving', plan: null, packs: {} }
const listeners = new Set()
const set = (next) => {
  state = { ...state, ...next }
  listeners.forEach((listener) => listener())
}
const setPack = (id, next) => set({ packs: { ...state.packs, [id]: { ...state.packs[id], ...next } } })

/** Start the worker, once, at page start. Nothing in dev: there the files change on every save. */
export function startOffline() {
  if (!supported()) return
  set({ supported: true })
  navigator.serviceWorker.register('/sw.js').catch(() => set({ core: 'none' }))
  navigator.serviceWorker.ready.then(() => set({ core: 'ready' }))
}

let planOnce = null
/** The built plan, and how much of each pack is already saved. Asked for when Settings opens. */
export function loadPacks() {
  if (!state.supported) return
  planOnce ??= fetch(PLAN_URL).then((res) => res.json()).then(async (plan) => {
    set({ plan })
    for (const pack of PACKS) {
      const files = plan.packs[pack.id]?.files ?? []
      const have = (await caches.has(PACK + pack.id)) ? (await (await caches.open(PACK + pack.id)).keys()).length : 0
      setPack(pack.id, { status: packState(have, files.length) })
    }
  }).catch(() => { planOnce = null })
}

/** Save every file of a pack, a few at a time; one already saved is skipped, so a retry resumes. */
export async function getPack(id) {
  const files = state.plan?.packs[id]?.files ?? []
  navigator.storage?.persist?.()
  const cache = await caches.open(PACK + id)
  let done = 0
  setPack(id, { status: 'getting', done, total: files.length })
  const queue = [...files]
  const worker = async () => {
    for (let url = queue.shift(); url; url = queue.shift()) {
      if (!(await cache.match(url))) {
        const response = await fetch(url)
        if (!response.ok) throw new Error(`${url}: ${response.status}`)
        await cache.put(url, response)
      }
      setPack(id, { done: ++done })
    }
  }
  try {
    await Promise.all(Array.from({ length: AT_ONCE }, worker))
    setPack(id, { status: 'ready' })
  } catch {
    queue.length = 0
    setPack(id, { status: 'failed' })
  }
}

export async function removePack(id) {
  await caches.delete(PACK + id)
  setPack(id, { status: 'none' })
}

const subscribe = (listener) => {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export const useOffline = () => useSyncExternalStore(subscribe, () => state, () => state)
