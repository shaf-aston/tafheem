/**
 * Where every bracket of a tarkeeb tree goes.
 *
 * Nothing about drawing is stored in the data. Two numbers per node do all the
 * work, the words it covers, and how many joins deep it is; and both are
 * worked out here from the tree's shape alone. Rows are levels, columns are
 * words, so a group covering 2 of 4 words is exactly half the width without
 * anything being measured.
 *
 * Pure: no DOM, no React. The component below it only turns this into elements.
 */

/** The API sends empty arrays where the artifact's data had nothing at all. */
export const kids = (node) => (node.children?.length ? node.children : null)
export const pieces = (node) => (node.parts?.length ? node.parts : null)
/**
 * A word named as its own first piece (يَصُمْهُ: فعل = فعل + فاعل + مفعول به) is no join
 * of its own, so its pieces are written in its parent's row, as the books write
 * لْـ + فعل + فاعل + مفعول به. A word whose pieces make up another job (خبر =
 * حرف جر + مجرور) keeps its own row.
 */
export const flat = (node) => !!pieces(node) && node.parts[0].role === node.role
const joins = (node) => kids(node) || (pieces(node) && !flat(node))

/**
 * A copy of the tree with `from`, `to` and `level` filled in.
 * `from`/`to` are word indexes; `level` is 0 for a plain word and counts up.
 */
export function measure(node) {
  const children = kids(node)?.map(measure)
  if (children) {
    return {
      ...node,
      children,
      from: Math.min(...children.map((c) => c.from)),
      to: Math.max(...children.map((c) => c.to)),
      level: 1 + Math.max(...children.map((c) => c.level)),
    }
  }
  // Pieces inside one written word are a join of their own, one level up.
  return { ...node, from: node.word, to: node.word, level: joins(node) ? 1 : 0 }
}

/** Every group, and every word carrying inner parts, keyed by its level. */
function byLevel(node, into = new Map()) {
  if (joins(node)) {
    if (!into.has(node.level)) into.set(node.level, [])
    into.get(node.level).push(node)
  }
  kids(node)?.forEach((child) => byLevel(child, into))
  return into
}

/** The level a word's role is written on, its parent's. Until then it threads. */
function roleLevels(node, parentLevel, into = {}) {
  // folded, several leaves share a column: it threads down to the last one named
  if (!kids(node)) into[node.word] = Math.max(into[node.word] ?? 0, parentLevel, node.level)
  kids(node)?.forEach((child) => roleLevels(child, node.level, into))
  return into
}

/** The columns whose leaf is understood, not written (ثابت in الحمد لله): a set of word indexes. */
export const hiddenWords = (node) =>
  kids(node) ? new Set(kids(node).flatMap((kid) => [...hiddenWords(kid)])) : new Set(node.hidden ? [node.word] : [])

/**
 * The whole diagram as rows, ready to render.
 *
 * Each row is one level of joining: the groups drawn on it, and the words that
 * have not been joined yet and so keep a thread running down to their own row.
 */
export function rows(tree, wordCount) {
  const measured = measure(tree)
  const groups = byLevel(measured)
  const wordRow = roleLevels(measured, measured.level)

  return Array.from({ length: measured.level }, (_, index) => {
    const level = index + 1
    const here = groups.get(level) ?? []
    const busy = new Set(here.flatMap((n) => Array.from({ length: n.to - n.from + 1 }, (_, i) => n.from + i)))
    const threads = Array.from({ length: wordCount }, (_, word) => word).filter(
      (word) => !busy.has(word) && wordRow[word] >= level,
    )
    return { level, groups: here, threads }
  })
}

/** A name to write: a group named only by its own brace (= متعلق بـ...) has none here. */
const named = (piece) => piece.role || piece.gap

/**
 * The names written on a group's row, each over the columns of its own words:
 * [{ from, to, roles }]. A flat word's pieces share its one column (لْـ | فعل + فاعل),
 * and a word's own pieces all sit over that word. Names that land on one column
 * (a folded word's pieces) share one cell, read in order with a "+" between.
 */
export const cells = (node) =>
  (kids(node)?.map((kid) => ({ from: kid.from, to: kid.to, roles: flat(kid) ? kid.parts : [kid] })) ??
    [{ from: node.from, to: node.to, roles: pieces(node) }])
    .map((cell) => ({ ...cell, roles: cell.roles.filter(named) }))
    .filter((cell) => cell.roles.length)
    .reduce((row, cell) => {
      const last = row.at(-1)
      if (last && cell.from <= last.to) Object.assign(last, { to: Math.max(last.to, cell.to), roles: [...last.roles, ...cell.roles] })
      else row.push(cell)
      return row
    }, [])

/** The tone of the word drawn in each column, so its underline is its name's colour. */
export function tones(node, into = []) {
  if (kids(node)) kids(node).forEach((kid) => tones(kid, into))
  else if (node.word != null) into[node.word] = node.gap ? 'gap' : node.tone
  return into
}

/**
 * The Merged view: every written word back in one column (فَـ إِذًا → فَإِذًا), its
 * pieces' names side by side in that column. The API always sends words cut into
 * pieces with `written` naming each piece's word; this is the only way back.
 */
export function fold({ words, written, tree }) {
  const folded = []
  const column = written.map((word, i) => {
    if (i > 0 && written[i - 1] === word) folded[folded.length - 1] += words[i]
    else folded.push(words[i])
    return folded.length - 1
  })
  const renumber = (node) =>
    kids(node) ? { ...node, children: node.children.map(renumber) } : node.word == null ? node : { ...node, word: column[node.word] }
  return { words: folded, written: folded.map((_, i) => i), tree: renumber(tree) }
}
