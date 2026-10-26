/**
 * Tafheem's offline worker. vite/offline.js writes the plan in at build, in place of the PLAN placeholder below;
 * src/config/offline.json holds the rules it was made from.
 *
 *  - The core (code, styles, fonts, icons) is saved when the worker installs, so the app opens with no signal.
 *  - Hashed files never change, so a saved one is used as is.
 *  - Other files (word lists, books) are shown from the phone at once and refreshed behind.
 *  - Server answers named in `keep` are asked for fresh; the saved copy stands in when there is
 *    no signal, the server is down, or it is slower than `wait` ms.
 *  - Packs are saved by the page (src/lib/shell/offline.js) into their own caches; this only reads them.
 */
const PLAN = self.__PLAN__
const CORE = `tafheem-core-${PLAN.version}`
const SEEN = 'tafheem-seen'
const OURS = 'tafheem-'
const SHELL = '/app.html'

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CORE).then((cache) => cache.addAll(PLAN.core)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(names.filter((name) => name.startsWith(`${OURS}core-`) && name !== CORE).map((name) => caches.delete(name))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin || url.pathname === '/sw.js') return
  if (request.mode === 'navigate') return event.respondWith(page(request, url))
  if (url.pathname.startsWith('/api/')) {
    if (PLAN.keep.some((prefix) => url.pathname.startsWith(prefix))) event.respondWith(fresh(request))
    return
  }
  event.respondWith(url.pathname.startsWith('/assets/') ? saved(request) : refreshed(event, request))
})

const find = (request) => caches.match(request, { ignoreVary: true })
const late = () => new Promise((done) => setTimeout(done, PLAN.wait, null))

/** Keep a whole, good answer in the seen cache, dropping the oldest past seen-max. */
async function keep(request, response) {
  if (response.status !== 200 || response.type !== 'basic') return
  const cache = await caches.open(SEEN)
  await cache.put(request.url, response)
  const keys = await cache.keys()
  await Promise.all(keys.slice(0, Math.max(0, keys.length - PLAN.seenMax)).map((key) => cache.delete(key)))
}

/** The network's answer, kept as it passes. */
const fetchKept = (request) => fetch(request).then((response) => {
  keep(request, response.clone())
  return response
})

/** A saved whole file, cut to the bytes asked for: audio asks for ranges, and Safari plays only a 206. */
async function ranged(request, response) {
  const range = /bytes=(\d*)-(\d*)/.exec(request.headers.get('range') ?? '')
  if (!range || response.status !== 200) return response
  const body = await response.blob()
  const from = Number(range[1] || 0)
  const to = range[2] ? Math.min(Number(range[2]), body.size - 1) : body.size - 1
  return new Response(body.slice(from, to + 1), {
    status: 206,
    headers: {
      'Content-Type': response.headers.get('Content-Type') ?? '',
      'Content-Range': `bytes ${from}-${to}/${body.size}`,
      'Content-Length': String(to - from + 1),
    },
  })
}

/** Every app page (all but the landing page and the recorder): from the network, or the saved shell when it cannot come. */
async function page(request, url) {
  const network = fetch(request)
  const app = url.pathname !== '/' && !url.pathname.startsWith('/record')
  const shell = app && await caches.match(SHELL)
  if (!shell) return network
  const first = await Promise.race([network.catch(() => null), late()])
  return first?.ok ? first : shell
}

/** A hashed file: the saved one if there is one. */
async function saved(request) {
  return (await find(request)) ?? fetchKept(request)
}

/** A plain file: the saved one now, refreshed in whichever cache holds it. */
async function refreshed(event, request) {
  const cached = await find(request)
  if (!cached) return fetchKept(request)
  event.waitUntil(fetch(request).then(async (response) => {
    if (response.status !== 200) return
    for (const name of (await caches.keys()).filter((one) => one.startsWith(OURS))) {
      const cache = await caches.open(name)
      if (await cache.match(request, { ignoreVary: true })) await cache.put(request.url, response.clone())
    }
  }).catch(() => {}))
  return ranged(request, cached)
}

/** A server answer: fresh when it comes in time and is good, else the saved copy. */
async function fresh(request) {
  const network = fetchKept(request)
  const cached = await find(request)
  if (!cached) return network.catch(() => Response.error())
  const first = await Promise.race([network.catch(() => null), late()])
  return first?.ok ? first : ranged(request, cached)
}
