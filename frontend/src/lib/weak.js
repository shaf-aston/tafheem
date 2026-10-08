/**
 * Where a hadith's chain may be weak, ranked by how weak.
 *
 * The server sends a note for each weak narrator in a hadith (`at`, `level`,
 * `kind`, `grade`) and the twelve levels once (`scale`). lib/rijal linked pins
 * each note to the narrator it names in the drawn chain, as `link.note`; this
 * turns those into a ranked list. Pure: no React.
 */

/** Every drawn narrator, the main strand and each branch with the narrator it joins at. */
const drawn = ({ main, branches }) => [...main, ...branches.flatMap((b) => [...b.links, b.join])].filter(Boolean)

/**
 * The weak narrators of a drawn chain, weakest first and, among equals, in the
 * order the chain is read. Equal levels share a rank (1, 2, 2, 4) and print as
 * `label`: "2=". A narrator drawn twice (a branch's join) counts once.
 */
export function weakPoints(links, scale) {
  const levels = new Map(scale.map((row) => [row.level, row]))
  const seen = new Set()
  const found = drawn(links).filter((link) => {
    if (!link.note || !levels.has(link.note.level) || seen.has(link.note.at)) return false
    seen.add(link.note.at)
    return true
  }).map((link) => ({ ...link.note, name: link.name, id: link.id ?? link.note.id }))
  found.sort((a, b) => b.level - a.level || a.at - b.at)
  return found.map((point) => {
    const row = levels.get(point.level)
    const rank = 1 + found.filter((other) => other.level > point.level).length
    const tied = found.some((other) => other !== point && other.level === point.level)
    return {
      ...point, rank, tied, label: `${rank}${tied ? '=' : ''}`,
      en: row.en, source: row.source, lift: row.lift[point.kind] ?? null,
    }
  })
}
