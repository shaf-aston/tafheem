import { describe, expect, it } from 'vitest'

import { familyTree, ROOT_NAME } from './familyTree'

const who = (id) => ({ id, name: `n${id}` })
// Text order: the book's teacher first, the Prophet's end last.
const chain = (...ids) => ids.map(who)

describe('familyTree', () => {
  it('merges shared top narrators, branches where chains differ, keeps letter order', () => {
    const tree = familyTree([
      { part: 'a', narrators: chain(1, 2, 3) },
      { part: 'b', narrators: chain(4, 2, 3) },
    ])
    // 3 and 2 once each, then 1 and 4: four nodes, two leaves in letter order.
    expect(tree.nodes.map((n) => n.name).sort()).toEqual(['n1', 'n2', 'n3', 'n4'])
    expect(tree.leaves.map((l) => [l.part, l.x])).toEqual([['a', 0], ['b', 1]])
    expect(tree.edges).toHaveLength(3)
  })

  it('puts different top narrators under one virtual root', () => {
    const tree = familyTree([
      { part: 'a', narrators: chain(1, 2) },
      { part: 'b', narrators: chain(1, 3) },
    ])
    expect(tree.nodes.some((n) => n.name === ROOT_NAME && n.depth === 0)).toBe(true)
  })
})
