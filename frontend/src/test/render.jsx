/**
 * Render a whole screen in a test: a fresh query cache and a fake backend.
 *
 * Every backend request goes through api.js's one axios client, so the fake
 * sits at its adapter and no api function is mocked one by one. `routes` maps
 * 'GET /path' to the data it answers (or a function of the request); a
 * request not listed fails as a 404, the way a backend that is down would,
 * so a screen's error state is part of what a smoke test sees. A plain fetch
 * is for the app's own static files (the word banks), so it is answered from
 * public/ on disk: the screen gets the real files it would get in the browser.
 *
 * Needs `// @vitest-environment happy-dom` at the top of the test file; the
 * rest of the suite stays on node.
 */
import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { afterEach } from 'vitest'
import { AxiosError } from 'axios'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render } from '@testing-library/react'

import { api } from '../api'

afterEach(cleanup)

const PUBLIC = join(import.meta.dirname, '../../public')

globalThis.fetch = async (input) => {
  const path = new URL(String(input?.url ?? input), 'http://app.test').pathname
  try {
    return new Response(await readFile(join(PUBLIC, path)), { headers: { 'Content-Type': 'application/json' } })
  } catch {
    return new Response('Not found', { status: 404 })
  }
}

export function renderScreen(ui, { routes = {} } = {}) {
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
  const view = render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
  return { ...view, client, asked }
}
