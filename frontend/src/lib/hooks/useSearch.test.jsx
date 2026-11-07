// @vitest-environment happy-dom
import { Activity, StrictMode } from 'react'
import { afterEach, describe, expect, it } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, cleanup, render, waitFor } from '@testing-library/react'

import { useSearch } from './useSearch'

// A request the test answers when it chooses, so a panel can be hidden mid-flight.
function deferred() {
  let answer
  const promise = new Promise((resolve) => { answer = resolve })
  return { promise, answer }
}

function setup({ strict = false } = {}) {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
  const pending = []
  const ask = ({ q }) => {
    const one = deferred()
    pending.push(one)
    return one.promise.then(() => ({ query: q }))
  }
  const result = {}
  const report = (now) => { result.current = now }
  function Probe() {
    report(useSearch({ historyKey: 'test-history', ask, incoming: 'كتب', arrival: 1 }))
    return null
  }
  const tree = (mode) => {
    const page = (
      <QueryClientProvider client={client}>
        <Activity mode={mode}><Probe /></Activity>
      </QueryClientProvider>
    )
    return strict ? <StrictMode>{page}</StrictMode> : page
  }
  const view = render(tree('visible'))
  return { result, pending, show: (mode) => view.rerender(tree(mode)) }
}

afterEach(cleanup)

describe('useSearch', () => {
  // StrictMode mounts, unmounts and mounts again in development. The arrival's
  // request was started in the first mount and its answer never reached the box.
  it('lands an arriving word under StrictMode', async () => {
    const { result, pending } = setup({ strict: true })
    await waitFor(() => expect(pending).toHaveLength(1))
    await act(async () => pending[0].answer())
    await waitFor(() => expect(result.current.mutation.isPending).toBe(false))
    expect(result.current.shown).toEqual({ query: 'كتب' })
  })

  it('asks an arriving word once under StrictMode', async () => {
    const { pending } = setup({ strict: true })
    await waitFor(() => expect(pending).toHaveLength(1))
    await act(async () => {})
    expect(pending).toHaveLength(1)
  })

  // The same tear-down happens in production when App hides a tab (Activity)
  // while its search is still out.
  it('lands a search that came back while its tab was hidden', async () => {
    const { result, pending, show } = setup()
    await waitFor(() => expect(pending).toHaveLength(1))
    act(() => result.current.submit('book'))
    await waitFor(() => expect(pending).toHaveLength(2))
    show('hidden')
    await act(async () => pending.forEach((one) => one.answer()))
    show('visible')
    await waitFor(() => expect(result.current.mutation.isPending).toBe(false))
    expect(result.current.shown).toEqual({ query: 'book' })
  })
})
