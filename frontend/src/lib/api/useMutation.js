/**
 * TanStack's useMutation, made to hold on to its request when React tears the
 * component's effects down and sets them up again while the request is out.
 *
 * React does that in two places. StrictMode mounts every component twice in
 * development, and App's Activity drops a hidden tab's effects and runs them
 * again when it is shown. Each time, TanStack's observer lets go of the request
 * it was following and never takes hold of it again, so the answer lands
 * unseen and the box spins for ever. A search asked on arrival (lib/nav/useArrival)
 * starts in the very effect StrictMode repeats, so in dev every one hung.
 *
 * Same arguments, same result, so it swaps in for the library's own.
 */
import { useCallback, useEffect, useState, useSyncExternalStore } from 'react'
import { MutationObserver, noop, notifyManager, useQueryClient } from '@tanstack/react-query'

class HeldObserver extends MutationObserver {
  constructor(client, options) {
    super(client, options)
    this.cache = client.getMutationCache()
  }

  mutate(variables, options) {
    const run = super.mutate(variables, options)
    // The request just built, which the parent keeps private.
    this.following = this.cache.getAll().at(-1)
    return run
  }

  reset() {
    this.following = undefined
    super.reset()
  }

  // Listened to again: take hold of the request again, and catch up on
  // whatever it did while no one was listening.
  onSubscribe() {
    if (!this.following) return
    this.following.addObserver(this)
    this.onMutationUpdate()
  }
}

export function useMutation(options) {
  const client = useQueryClient()
  const [observer] = useState(() => new HeldObserver(client, options))
  useEffect(() => { observer.setOptions(options) }, [observer, options])

  const result = useSyncExternalStore(
    useCallback((changed) => observer.subscribe(notifyManager.batchCalls(changed)), [observer]),
    () => observer.getCurrentResult(),
    () => observer.getCurrentResult(),
  )
  const mutate = useCallback((variables, more) => { observer.mutate(variables, more).catch(noop) }, [observer])
  return { ...result, mutate, mutateAsync: result.mutate }
}
