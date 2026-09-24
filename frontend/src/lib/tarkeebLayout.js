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
const kids = (node) => (node.children?.length ? node.children : null)
const pieces = (node) => (node.parts?.length ? node.parts : null)

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
  return { ...node, from: node.word, to: node.word, level: pieces(node) ? 1 : 0 }
}

/** Every group, and every word carrying inner parts, keyed by its level. */
function byLevel(node, into = new Map()) {
  if (kids(node) || pieces(node)) {
    if (!into.has(node.level)) into.set(node.level, [])
    into.get(node.level).push(node)
  }
  kids(node)?.forEach((child) => byLevel(child, into))
  return into
}

/** The level a word's role is written on, its parent's. Until then it threads. */
function roleLevels(node, parentLevel, into = {}) {
  if (!kids(node)) into[node.word] = Math.max(parentLevel, node.level)
  kids(node)?.forEach((child) => roleLevels(child, node.level, into))
  return into
}

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

/**
 * How wide a piece sits in its parent's row. A group covering two of its
 * parent's four words takes two shares; a single word takes one.
 */
export const share = (piece) =>
  kids(piece) || pieces(piece) ? piece.to - piece.from + 1 : 1

/**
 * Split a ghair-عامل connector (فَ / وَ) off the word it is glued to, so it
 * draws as its own labelled column instead of a "+" fused into the word
 * after it. Off by default, a reader who wants to see it separately asks.
 *
 * The backend never splits a written word itself; it only marks which piece
 * of a compound is the connector (`ghair_aamil: true`) and, on that word,
 * the connector's own exact text (`prefix_arabic`). Turning that into two
 * grid columns is display policy, so it happens here rather than in the API.
 */
export function splitConnectors(words, tree) {
  const splits = new Map() // original word index -> { text, piece }
  const find = (node) => {
    if (node.children?.length) return node.children.forEach(find)
    if (node.word == null || !node.prefix_arabic || !node.parts?.length) return
    const piece = node.parts.find((p) => p.ghair_aamil)
    if (piece) splits.set(node.word, { text: node.prefix_arabic, piece })
  }
  find(tree)
  if (splits.size === 0) return { words, tree, terms: [] }

  const newWords = []
  const wordAt = []       // original index -> new index of the word's own remainder
  const connectorAt = []  // original index -> new index of the connector, when split
  words.forEach((full, i) => {
    const split = splits.get(i)
    if (split && full.startsWith(split.text) && split.text.length < full.length) {
      connectorAt[i] = newWords.length
      newWords.push(split.text)
    }
    wordAt[i] = newWords.length
    newWords.push(connectorAt[i] === undefined ? full : full.slice(split.text.length))
  })

  const rewrite = (node) => {
    if (node.children?.length) return [{ ...node, children: node.children.flatMap(rewrite) }]
    if (node.word == null) return [node]
    const split = splits.get(node.word)
    if (!split || connectorAt[node.word] === undefined) return [{ ...node, word: wordAt[node.word] }]

    const rest = node.parts.filter((p) => p !== split.piece)
    const remainder = { ...node, word: wordAt[node.word] }
    delete remainder.prefix_arabic
    if (rest.length > 1) {
      remainder.parts = rest
    } else {
      remainder.role = rest[0].role
      remainder.tone = rest[0].tone
      remainder.parts = []
    }
    const connector = {
      word: connectorAt[node.word],
      role: split.piece.role,
      tone: split.piece.tone,
      detail: split.piece.detail,
      ghair_aamil: true,
      parts: [],
      children: [],
    }
    return [connector, remainder]
  }

  return {
    words: newWords,
    tree: { ...tree, children: tree.children.flatMap(rewrite) },
    terms: [...new Set([...splits.values()].map((s) => s.piece.role))],
  }
}
