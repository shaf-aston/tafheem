/** Grow's worlds as worlds.json lists them, each with its theme accent, and the record each files its answers under (its `module`, named there only). */
import config from '../../config/worlds.json'
import { colorFor } from '../../theme'

export const WORLDS = config.worlds.map((world) => ({ ...world, accent: colorFor('world', world.id) }))

export const worldOf = (id) => WORLDS.find((world) => world.id === id) ?? null

/** The record world `id` files its answers under; null for no such world. */
export const moduleOf = (id) => worldOf(id)?.module ?? null

// Which worlds are which kind — the one place GrowPanel.jsx reads this split from, instead
// of each re-deriving its own filter. A book world needs nothing further: BookWorld reads its
// `source` generically. A lessons world's hook is still a separate line GrowPanel must call
// (React won't let a hook be called from a loop or a table), so missingLessonHooks below is
// what keeps a forgotten one from failing silently instead.
export const WORLD_IDS = WORLDS.filter((world) => world.live).map((world) => world.id)
export const LESSON_WORLD_IDS = WORLDS.filter((world) => world.kind === 'lessons').map((world) => world.id)
export const BOOKS = WORLDS.filter((world) => world.kind === 'book')
export const BOOK_IDS = BOOKS.map((world) => world.id)

/** Any `kind: "lessons"` world in worlds.json with no hook in GrowPanel's `lessons` map —
 *  the thing that used to crash deep inside SCREENS/LessonWorld with no clue why. */
export const missingLessonHooks = (lessons) => LESSON_WORLD_IDS.filter((id) => !(id in lessons))
