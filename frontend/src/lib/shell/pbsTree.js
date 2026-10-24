/**
 * A chart as a tree that can be entered at any depth, pure data.
 *
 * Levels 1-3 come from the chart config (root, branches, kids). Below a kid,
 * children come from lib/pbsDeep's DEEP["<path>"], else, for a kid, from its
 * SUB "·" list (Arabic only). DEEP may also hold any deeper path. Children
 * inherit the nearest ancestor's colour `c`.
 */
import { SUB } from './pbsData'
import { DEEP } from './pbsDeep'

const fromSub = (text) => text.split('·').map((t) => t.trim()).filter(Boolean).map((ar) => [ar, ''])

/** Drop exact-duplicate Arabic entries, keeping the first. */
function unique(pairs) {
  const seen = new Set()
  return pairs.filter(([ar]) => !seen.has(ar) && seen.add(ar))
}

function node(ar, en, c, key, own, deep, sub) {
  const listed = deep[key] ?? own ?? (sub[key] ? fromSub(sub[key]) : [])
  return { ar, en, c, kids: unique(listed).map(([a, e], i) => node(a, e, c, `${key}.${i}`, null, deep, sub)) }
}

export function chartTree(chart, deep = DEEP, sub = SUB) {
  const { root, branches } = chart.config
  return {
    ar: root.ar,
    en: root.en,
    kids: branches.map((b, i) => {
      const key = `${chart.id}.${i}`
      const kids = deep[key] ?? b.kids
      return {
        ar: b.ar,
        en: b.en,
        c: b.c,
        kids: unique(kids).map(([a, e], j) => node(a, e, b.c, `${key}.${j}`, null, deep, sub)),
      }
    }),
  }
}

/** The node at a path of child indices, or null if any step is out of range. */
export function nodeAt(tree, path) {
  let n = tree
  for (const i of path) {
    n = n?.kids[i]
    if (!n) return null
  }
  return n
}

/** A PbsChart config showing `n` as root; kids carry a third `hasKids` flag. */
export function viewConfig(n, footnote = []) {
  return {
    root: { ar: n.ar, en: n.en },
    branches: n.kids.map((b) => ({
      ar: b.ar,
      en: b.en,
      c: b.c,
      hasKids: b.kids.length > 0,
      kids: b.kids.map((g) => [g.ar, g.en, g.kids.length > 0]),
    })),
    footnote,
  }
}
