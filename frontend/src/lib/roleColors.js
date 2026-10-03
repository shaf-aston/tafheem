import { colorFor } from '../theme'

/**
 * A role's colour comes from the backend's `role_key`, never from searching the
 * Arabic prose beside it (that matched nothing and greyed every word). No key, grey.
 */

/** The theme token for a role, or the neutral one when there is no role. */
export const roleVar = (key) => `var(--role-${key || 'default'})`

/** The colour for a corpus part-of-speech code on the Quran tab. */
export const posColor = (tag) => colorFor('pos', tag)
