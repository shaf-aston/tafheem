/**
 * Walking a chart's tree (lib/shell/pbsData's `chart.tree`), pure data.
 * A tree can be entered at any depth: a path of child indices names a node,
 * and `viewConfig` turns that node into what PbsChart draws.
 */

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
