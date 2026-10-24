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

/** Put an ayah's row at the top of the list, moving the list and not the page. */
export function showRow(list, ayah) {
  const row = list?.children[ayah - 1]
  if (row) list.scrollTop = row.offsetTop
}
