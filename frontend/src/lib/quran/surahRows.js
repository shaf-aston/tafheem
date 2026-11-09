/** The ayah whose row is at the top of the list, counting from 1. Rows are
 *  in ayah order, so a binary search over their offsets. */
export function rowAt(list) {
  const rows = list.children
  let lo = 0
  let hi = rows.length - 1
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1
    if (rows[mid].offsetTop <= list.scrollTop + 8) lo = mid
    else hi = mid - 1
  }
  return lo + 1
}

/** Put an ayah's row at the top of the list, `into` px down it, moving the list and not the page. */
export function showRow(list, ayah, into = 0) {
  const row = list?.children[ayah - 1]
  if (row) list.scrollTop = row.offsetTop + into
}

/** Where the list is now, as a row and how far into it: what showRow puts back, whatever the rows around it do. */
export function lookingAt(list) {
  const row = rowAt(list)
  return { ayah: row, into: Math.max(0, list.scrollTop - (list.children[row - 1]?.offsetTop ?? 0)) }
}
