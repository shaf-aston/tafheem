/**
 * How many grid columns each small dictionary card takes, worked out for the
 * whole set at once so every row is full.
 *
 * Width only helps a card whose lines wrap: eight short senses are as tall in
 * two columns as in one, the extra width is empty. So a card asks for two
 * columns only when that saves it two lines or more, or it carries a synonym
 * band. Rows are then chosen over the whole set, so none ends in a gap and no
 * card sits alone across the page. dictionary.json is read only here.
 */
import config from '../dictionary.json'

const { 'wrap-letters': WRAP } = config.forms

/** Lines a card's senses wrap onto beyond one each, at one column's width. */
const extraLines = (entry) => (entry.definitions ?? []).reduce((n, d) => n + Math.ceil(d.length / WRAP) - 1, 0)
const hasSynonyms = (entry) => (entry.synonyms ?? []).some((list) => list.length > 0)

/** Columns a card wants on its own: 2 when width would save it two lines or more, or it has synonyms. */
const want = (entry) => (hasSynonyms(entry) || extraLines(entry) >= 2 ? 2 : 1)

/**
 * @returns {number[]} one span per entry, each 1..cols, every row summing to cols.
 * Row breaks keep the order and are chosen for fewest rows, then the most even
 * rows (least spare room, squared), so seven cards in three columns go 3·2·2,
 * never 3·3 and one card alone. A row's spare columns go to its card that wraps most.
 */
export function entrySpans(entries, cols) {
  const wants = entries.map((e) => Math.min(want(e), cols))
  // best[i]: cheapest layout of the first i cards, as [rows, waste, start of last row].
  const best = [[0, 0, 0]]
  for (let i = 1; i <= entries.length; i++) {
    let used = 0
    for (let j = i - 1; j >= 0 && (used += wants[j]) <= cols; j--) {
      const cand = [best[j][0] + 1, best[j][1] + (cols - used) ** 2, j]
      if (!best[i] || cand[0] < best[i][0] || (cand[0] === best[i][0] && cand[1] < best[i][1])) best[i] = cand
    }
  }
  const spans = [...wants]
  for (let end = entries.length; end > 0; end = best[end][2]) {
    const row = spans.slice(best[end][2], end).map((_, k) => best[end][2] + k)
    for (let gap = cols - row.reduce((n, k) => n + wants[k], 0); gap > 0; gap--) {
      spans[row.reduce((a, b) => (extraLines(entries[b]) > extraLines(entries[a]) ? b : a))]++
    }
  }
  return spans
}
