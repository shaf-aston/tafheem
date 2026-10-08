/**
 * Where a hadith's chain may be weak, ranked by how weak.
 *
 * The server sends a note for each weak narrator in a hadith (`at`, `level`,
 * `kind`, `grade`) and the twelve levels once (`scale`). lib/rijal linked pins
 * each note to the narrator it names in the drawn chain, as `link.note`; this
 * turns those into a ranked list. It also sends the links a source puts in
 * doubt (`ties`, pinned the same way) with what each kind says (`rules`); those
 * are listed in chain order and never ranked against the narrators. Pure: no React.
 */

/** Every drawn narrator, the main strand and each branch with the narrator it joins at. */
const drawn = ({ main, branches }) => [...main, ...branches.flatMap((b) => [...b.links, b.join])].filter(Boolean)

/**
 * The weak narrators of a drawn chain, weakest first and, among equals, in the
 * order the chain is read. Equal levels share a rank (1, 2, 2, 4) and print as
 * `label`: "2=". A narrator named twice (a branch's join, or two strands) counts once.
 */
export function weakPoints(links, scale) {
  const levels = new Map(scale.map((row) => [row.level, row]))
  const seen = new Set()
  const found = drawn(links).filter((link) => {
    if (!link.note || !levels.has(link.note.level) || seen.has(link.note.id)) return false
    seen.add(link.note.id)
    return true
  }).map((link) => ({ ...link.note, name: link.name, id: link.note.id }))
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

/**
 * The links of a drawn chain a source puts in doubt, top of the drawing first
 * (the narrator nearest the Prophet comes last in the text) and, at one place,
 * the teller with the higher tadlis level first. Each has a letter, the mark
 * on its rung in the drawing, and the lines the list prints: its kind, the
 * condition it meets and the quotes with their book and page.
 *
 * A tie is kept only if the teller (`student`) is also drawn, so both names can
 * be printed. Points are keyed by who said it to whom, never by position: a
 * narrator named in two strands is one point (like weakPoints), but the same
 * two men in two places in one chain are one link too.
 */
export function weakLinks(links, rules) {
  if (!rules) return []
  const all = drawn(links)
  const named = new Map(all.filter((link) => link.id != null).map((link) => [link.id, link]))
  const seen = new Set()
  const found = []
  for (const teacher of all) {
    for (const tie of teacher.ties ?? []) {
      const kind = rules.kinds[tie.kind === 'not_heard' ? tie.sub : tie.kind]
      const student = named.get(tie.student)
      const key = [tie.student, tie.teacher, tie.kind, tie.sub, tie.quote].join('>')
      if (!kind || !student || seen.has(key)) continue
      seen.add(key)
      const tadlis = tie.kind !== 'not_heard'
      found.push({
        ...tie, key, label: kind.label, teller: student.name, teacherName: teacher.name,
        says: tadlis ? [kind.say, rules.levels[tie.level]?.say].filter(Boolean) : [kind.say],
        quotes: (tadlis ? [rules.levels[tie.level], kind, rules.skip] : [{ quote: tie.quote, source: tie.source, page: tie.page }])
          .filter((q) => q?.quote),
      })
    }
  }
  found.sort((a, b) => b.at - a.at || b.level - a.level)
  return found.map((point, i) => ({ ...point, letter: i < 26 ? String.fromCharCode(97 + i) : String(i + 1) }))
}
