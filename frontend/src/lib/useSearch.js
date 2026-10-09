/**
 * One search box's wiring, as the Dictionary, Daleel and Hadith share it: the
 * typed query, its Recent list, the request, and a query arriving from another
 * tab or the back arrow (lib/useArrival), which goes in the box and is asked.
 *
 * `ask` gets `{ q, ...more }` as `submit(q, more)` builds it. A search that
 * comes back is a place reached (lib/journey.js): `place` names it, the typed
 * words unless the server spelt them its own way, and it goes in Recent and to
 * `onVisit(place, data)`. The Qur'an box first reads whether a line is a place
 * or words (lib/quranIntent), so it keeps its own.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { useArrival, useArrivalEffect, useHeld } from './useArrival'
import { useHistory } from './useHistory'

const typed = (_, { q }) => q

export function useSearch({ historyKey, ask, place = typed, onVisit, incoming, arrival }) {
  const [query, setQuery] = useState(incoming ?? '')
  const { history, push: remember } = useHistory(historyKey)

  const mutation = useMutation({
    mutationFn: ask,
    onSuccess: (data, asked) => {
      const reached = place(data, asked)
      remember({ q: reached })
      onVisit?.(reached, data)
    },
  })

  // Followed during the render, so the box never shows the old query for a frame.
  const { arrived, returning } = useArrival(arrival, mutation.isPending)
  if (arrived && incoming) setQuery(incoming)
  useArrivalEffect(arrival, () => {
    if (incoming) mutation.mutate({ q: incoming })
  })

  // A query handed in (a Recent chip, the microphone, a linked word) is put in
  // the box too, so the reader sees what was asked and can edit it.
  const submit = (given, more) => {
    const q = (given ?? query).trim()
    if (!q) return
    if (given !== undefined) setQuery(given)
    mutation.mutate({ q, ...more })
  }

  const clear = () => {
    setQuery('')
    mutation.reset()
  }

  // Through a return the answer already read stays up until the new one lands.
  const shown = useHeld(mutation.isPending ? undefined : mutation.data, returning)

  return { query, setQuery, history, mutation, submit, clear, shown }
}
