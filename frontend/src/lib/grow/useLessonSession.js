/**
 * A lesson being played from a world (lib/grow/useLessonWorld.js, lib/grow/useBookWorld.js), the same in Grow and in the
 * Quiz's Basics: its cards are dealt once, from a record that has caught up with every answer, and held while it is
 * played.
 *
 * `playing` is `{ world, key }` (the world's id, and a key that changes whenever another lesson starts) or null when
 * none is; `worlds` finds a world's data by id; `deal(world)` makes that world's cards. Gives back the cards: null until
 * dealt, [] when there was nothing to deal.
 *
 * The world is told it `began` once its cards are on screen. Once a lesson is left, by whatever way, its world's record
 * is re-read and the next lesson waits for it, so the items just answered are not offered again as new; a record left
 * behind by answers elsewhere (the world's `behind`) is caught up the same way before a lesson is dealt from it.
 */
import { useEffect, useEffectEvent, useState } from 'react'

const NONE = { key: null, world: null, cards: null }

export function useLessonSession(worlds, playing, deal) {
  const [held, setHeld] = useState(NONE)
  // The world whose record is being re-read after a lesson there; nothing is dealt meanwhile.
  const [owed, setOwed] = useState(null)
  const key = playing?.key ?? null
  const left = held.key !== null && held.key !== key
  if (left) {
    setHeld(NONE)
    if (held.cards.length) setOwed(held.world)
  }
  const world = playing && worlds(playing.world)
  // A lesson asked for and not yet dealt (none is while a record is being re-read).
  const wanted = Boolean(world) && !left && held.key !== key && owed === null
  if (wanted && world.dealable) setHeld({ key, world: playing.world, cards: deal(world) ?? [] })

  const refresh = useEffectEvent((id) => worlds(id).refresh())
  useEffect(() => {
    if (owed !== null) Promise.resolve(refresh(owed)).finally(() => setOwed(null))
  }, [owed])

  const behind = wanted && world.behind ? playing.world : null
  useEffect(() => { if (behind) refresh(behind) }, [behind])

  const on = Boolean(held.cards?.length)
  const begin = useEffectEvent((id) => worlds(id).began?.())
  useEffect(() => { if (on) begin(held.world) }, [on, held.key, held.world])

  return held.cards
}
