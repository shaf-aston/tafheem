/**
 * Levenshtein edit distance between two strings. With `max`, once every entry
 * in a row exceeds it the words cannot match, so it stops and returns max + 1
 * rather than finishing the table. Without `max` the result is exact.
 */
export function editDistance(a, b, max = Infinity) {
  if (Math.abs(a.length - b.length) > max) return max + 1
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i)
  for (let i = 1; i <= a.length; i++) {
    const row = [i]
    let rowMin = i
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1
      const value = Math.min(row[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
      row.push(value)
      rowMin = Math.min(rowMin, value)
    }
    if (rowMin > max) return max + 1
    prev = row
  }
  return prev[b.length]
}
