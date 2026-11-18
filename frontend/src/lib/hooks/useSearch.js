/**
 * One search box's wiring, as the Dictionary, Daleel and Hadith share it: the
 * typed query, its Recent list, the request, and a query arriving from another
 * tab or the back arrow (lib/nav/useArrival), which goes in the box and is asked.
 *
 * `ask` gets `{ q, ...more }` as `submit(q, more)` builds it. A search that
 * comes back is a place reached (lib/nav/journey.js): `place` names it, the typed
 * words unless the server spelt them its own way, and it goes in Recent and to
 * `onVisit(place)`, and the answer to `onFound(data)`. The Qur'an box first reads whether a line is a place
 * or words (lib/quranIntent), so it keeps its own.
 */
import { useState } from 'react'
import { useMutation } from '../api/useMutation'

import { useArrival, useArrivalEffect, useHeld } from '../nav/useArrival'
import { useHistory } from '../nav/useHistory'

const typed = (_, { q }) => q

// Only the place goes to `onVisit`: its second argument means "moves on within the same
// step" (lib/nav/journey.js), and the answer handed there made every search take the
// previous one's place, so back skipped it.
export function useSearch({ historyKey, ask, place = typed, onVisit, onFound, incoming, arrival }) {
  const [query, setQuery] = useState(incoming ?? '')
  const { history, push: remember } = useHistory(historyKey)

  const mutation = useMutation({
    mutationFn: ask,
    onSuccess: (data, asked) => {
      const reached = place(data, asked)
      remember({ q: reached })
      onVisit?.(reached)
      onFound?.(data)
    },
  })

  // Followed during the render, so the box never shows the old query for a frame.
  const { arrived, returning } = useArrival(arrival, mutation.isPending)
  // An arrival with nothing (back to the tab's top page, the tab chosen again) empties it.
  if (arrived) setQuery(incoming ?? '')
  useArrivalEffect(arrival, () => {
    if (incoming) mutation.mutate({ q: incoming })
    else mutation.reset()
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
  const shown = useHeld(mutation.isPending ? undefined : mutation.data, returning && Boolean(incoming))

  return { query, setQuery, history, mutation, submit, clear, shown }
}
