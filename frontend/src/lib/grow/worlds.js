/** Grow's worlds as worlds.json lists them, each with its theme accent, and the record each files its answers under (its `module`, named there only). */
import config from '../../config/worlds.json'
import { colorFor } from '../../theme'

export const WORLDS = config.worlds.map((world) => ({ ...world, accent: colorFor('world', world.id) }))

export const worldOf = (id) => WORLDS.find((world) => world.id === id) ?? null

/** The record world `id` files its answers under; null for no such world. */
export const moduleOf = (id) => worldOf(id)?.module ?? null
