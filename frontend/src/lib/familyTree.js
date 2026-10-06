/**
 * One tree from a family's chains, as a trie of the chains read from the Prophet's end:
 * narrators two chains share down from the top are one node, each narration branches
 * off where it differs and ends in a leaf (its letter). Chains that start from different
 * top narrators hang under one virtual root. Leaves take consecutive columns in letter
 * order and a node sits over the middle of what hangs from it, so no line crosses.
 * Pure layout in grid units; the drawing scales them.
 */
export const ROOT_NAME = 'النبي ﷺ'

export function familyTree(parts) {
  const root = { key: 'root', id: null, name: ROOT_NAME, depth: 0, kids: new Map(), leaves: [] }
  for (const { part, narrators } of [...parts].sort((a, b) => a.part.localeCompare(b.part))) {
    let at = root
    ;[...narrators].reverse().forEach((who, i) => {
      if (!at.kids.has(who.id)) at.kids.set(who.id, { key: `${at.key}/${who.id}`, id: who.id, name: who.name, depth: i + 1, kids: new Map(), leaves: [] })
      at = at.kids.get(who.id)
    })
    at.leaves.push(part)
  }
  // A single top narrator is the root itself, so the virtual one is dropped.
  const top = root.kids.size === 1 && !root.leaves.length ? [...root.kids.values()][0] : root
  const first = (node) => [...node.leaves, ...[...node.kids.values()].map(first)].sort()[0]

  const nodes = []
  const edges = []
  const leaves = []
  let column = 0
  const place = (node, depth) => {
    node.depth = depth
    // Own leaves and sub-branches, in the order of the first letter under each.
    const items = [...node.leaves.map((part) => ({ part, first: part })), ...[...node.kids.values()].map((n) => ({ n, first: first(n) }))]
      .sort((a, b) => a.first.localeCompare(b.first))
    const xs = items.map((item) => {
      if (item.part) {
        leaves.push({ part: item.part, parent: node.key, x: column })
        return column++
      }
      edges.push([node.key, item.n.key])
      return place(item.n, depth + 1)
    })
    node.x = (Math.min(...xs) + Math.max(...xs)) / 2
    nodes.push({ key: node.key, name: node.name, depth, x: node.x })
    return node.x
  }
  place(top, 0)
  const rows = Math.max(...nodes.map((n) => n.depth)) + 1
  return { nodes, edges, leaves: leaves.map((l) => ({ ...l, y: rows })), rows, columns: column }
}
