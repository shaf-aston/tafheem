/**
 * Render a whole screen (or one hook) in a test: a fresh query cache and a fake backend.
 *
 * Every backend request goes through api.js's one axios client, so the fake
 * sits at its adapter and no api function is mocked one by one. `routes` maps
 * 'GET /path' to the data it answers (or a function of the request); a
 * request not listed fails as a 404, the way a backend that is down would,
 * so a screen's error state is part of what a smoke test sees. A plain fetch
 * is for the app's own static files (the word banks), so it is answered from
 * public/ on disk: the screen gets the real files it would get in the browser,
 * a book world's split index and parts included (lib/grow/bookSplit.js).
 *
 * Needs `// @vitest-environment happy-dom` at the top of the test file; the
 * rest of the suite stays on node.
 */
import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { afterEach } from 'vitest'
import { AxiosError } from 'axios'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, renderHook } from '@testing-library/react'

import { api } from '../api'
import { servedFile } from '../lib/grow/bookSplit'

afterEach(cleanup)

const PUBLIC = join(import.meta.dirname, '../../public')

// A book world's index and parts are made from its authored file, as vite/growBooks.js serves them.
const BOOK_FILE = /^\/grow\/([\w-]+)\/([\w-]+\.json)$/

async function publicFile(path) {
  const [, name, file] = path.match(BOOK_FILE) ?? []
  if (!name) return readFile(join(PUBLIC, path))
  const body = servedFile(JSON.parse(await readFile(join(PUBLIC, `grow/${name}.json`), 'utf8')), file)
  if (!body) throw new Error('Not a part of this book')
  return JSON.stringify(body)
}

globalThis.fetch = async (input) => {
  const path = new URL(String(input?.url ?? input), 'http://app.test').pathname
  try {
    return new Response(await publicFile(path), { headers: { 'Content-Type': 'application/json' } })
  } catch {
    return new Response('Not found', { status: 404 })
  }
}

// A fresh query cache, and the axios adapter answering from `routes`.
function fakeBackend(routes) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  const asked = []
  api.defaults.adapter = async (config) => {
    const key = `${config.method.toUpperCase()} ${config.url}`
    asked.push(key)
    const reply = routes[key]
    if (reply === undefined) {
      const response = { status: 404, statusText: 'Not Found', data: { detail: 'Not found' }, headers: {}, config }
      throw new AxiosError('Not Found', AxiosError.ERR_BAD_REQUEST, config, null, response)
    }
    const data = typeof reply === 'function' ? reply(config) : reply
    return { status: 200, statusText: 'OK', data, headers: {}, config }
  }
  const wrapper = ({ children }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>
  return { client, asked, wrapper }
}

export function renderScreen(ui, { routes = {} } = {}) {
  const { client, asked, wrapper } = fakeBackend(routes)
  return { ...render(ui, { wrapper }), client, asked }
}

/** The same, for a hook on its own: `result.current` is what it returned. */
export function renderWithBackend(hook, { routes = {}, initialProps } = {}) {
  const { client, asked, wrapper } = fakeBackend(routes)
  return { ...renderHook(hook, { wrapper, initialProps }), client, asked }
}
