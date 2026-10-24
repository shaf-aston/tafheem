/**
 * The offline plan, made from what the build actually wrote (src/config/offline.json says the rules).
 *
 * After the build, every file in dist is sorted: a pack claims it, core-skip drops it, or it is
 * core. The plan goes two places: into sw.js (vite/sw.template.js), which saves the core on the
 * first visit, and into offline-files.json, which Settings reads to offer the packs. The version
 * is a hash of the core's names: a deploy that changes any file gives a new worker, so the phone
 * picks it up, and an unchanged deploy leaves the phone's copy alone.
 */
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative, sep } from 'node:path'

import knobs from '../src/config/offline.json' with { type: 'json' }

const TEMPLATE = join(import.meta.dirname, 'sw.template.js')
const OUT = { worker: 'sw.js', plan: 'offline-files.json' }

/** `[{ path, bytes }]` for every file under `dir`, paths relative and with forward slashes. */
function walk(dir, root = dir) {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name)
    return statSync(full).isDirectory()
      ? walk(full, root)
      : [{ path: relative(root, full).split(sep).join('/'), bytes: statSync(full).size }]
  })
}

const sum = (files) => files.reduce((total, file) => total + file.bytes, 0)

/**
 * Pure: the plan for these built files. An authored book whose split copy is also there
 * (grow/x.json beside grow/x/index.json, vite/growBooks.js) is never fetched, so no pack keeps it.
 */
export function planOffline(files, rules = knobs) {
  const ours = files.filter((file) => !Object.values(OUT).includes(file.path))
  const paths = new Set(ours.map((file) => file.path))
  const fetched = ours.filter((file) => !paths.has(file.path.replace(/\.json$/, '/index.json')))
  const packs = {}
  const claimed = new Set()

  for (const pack of rules.packs) {
    if (pack.api) {
      const urls = Array.from({ length: pack.count }, (_, i) => pack.api.replace('{n}', i + 1))
      packs[pack.id] = { files: urls, bytes: pack.bytes }
      continue
    }
    const mine = fetched.filter((file) => new RegExp(pack.match).test(file.path))
    for (const file of mine) claimed.add(file.path)
    packs[pack.id] = { files: mine.map((file) => `/${file.path}`), bytes: sum(mine) }
  }

  const skip = new RegExp(rules['core-skip'])
  const core = ours.filter((file) => !claimed.has(file.path) && !skip.test(file.path))
    .filter((file) => !/\.json$/.test(file.path) || fetched.includes(file))
  const version = createHash('sha1').update(core.map((file) => file.path).join('\n')).digest('hex').slice(0, 12)

  return {
    version,
    wait: rules['wait-ms'],
    seenMax: rules['seen-max'],
    keep: rules.keep,
    core: core.map((file) => `/${file.path}`),
    coreBytes: sum(core),
    packs,
  }
}

export const offline = {
  name: 'offline',
  apply: 'build',
  writeBundle({ dir }) {
    const plan = planOffline(walk(dir))
    const worker = readFileSync(TEMPLATE, 'utf8').replace('self.__PLAN__', JSON.stringify(plan))
    writeFileSync(join(dir, OUT.worker), worker)
    writeFileSync(join(dir, OUT.plan), JSON.stringify(plan))
  },
}
