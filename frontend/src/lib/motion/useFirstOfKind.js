/**
 * True for the first of its kind on screen, false for the rest.
 *
 * Some things should appear once however many components ask for them: the
 * qalam writing in a loading placeholder is a pen, not a row of pens, when one
 * screen waits on two answers at once. Each caller joins a queue for `kind`
 * when it mounts and leaves when it unmounts (a hidden tab's Activity unmounts
 * its effects too), and the oldest one holds the turn.
 */
import { useEffect, useId, useSyncExternalStore } from 'react'

const queues = new Map()
const listeners = new Set()
const changed = () => listeners.forEach((listener) => listener())
const queueOf = (kind) => queues.get(kind) ?? queues.set(kind, []).get(kind)

export function useFirstOfKind(kind) {
  const id = useId()
  useEffect(() => {
    queueOf(kind).push(id)
    changed()
    return () => {
      const queue = queueOf(kind)
      queue.splice(queue.indexOf(id), 1)
      changed()
    }
  }, [kind, id])
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    () => queueOf(kind)[0] === id,
    () => false,
  )
}
