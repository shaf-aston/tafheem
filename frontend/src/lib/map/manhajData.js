/**
 * The Map's methodologies section: Muslim schools and movements, grouped into
 * four families, each family answering one fixed list of questions.
 *
 * Why a fixed list per family: two groups can only be compared fairly when
 * both answer the same question. Each answer is `[tag, text]`. `tag` is a
 * short code that two groups share exactly when they hold the same position,
 * so "do these differ?" is a tag comparison, never a judgement made in the
 * view. `"n/a"` means the group has no settled position on that question; it
 * is never counted as agreement or difference.
 *
 * `self` is how the group describes itself; `beliefs` are its core claims as
 * its own main texts state them (`texts`). Where a group's position is
 * contested even among its own scholars, or is known only through opponents'
 * reports, `note` says so. Summaries are simplified for a first map, written
 * from these texts' well-known contents, not quoted from an edition.
 */

import creed from './manhaj/creed.json'
import fiqh from './manhaj/fiqh.json'
import sufi from './manhaj/sufi.json'
import modern from './manhaj/modern.json'

export const FAMILIES = [creed, fiqh, sufi, modern]

/** For one question, the other groups in the family holding the same position. */
export function sharedWith(family, group, qid) {
  const tag = group.positions[qid]?.[0]
  if (!tag || tag === 'n/a') return []
  return family.groups.filter((g) => g !== group && g.positions[qid]?.[0] === tag)
}

/** Whether two groups differ on a question; null when either has no position. */
export function differs(a, b, qid) {
  const ta = a.positions[qid]?.[0], tb = b.positions[qid]?.[0]
  if (!ta || !tb || ta === 'n/a' || tb === 'n/a') return null
  return ta !== tb
}
