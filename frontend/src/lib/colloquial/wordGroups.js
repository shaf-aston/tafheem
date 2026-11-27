// Words under their category headings, shared by the word bank and a topic's word grid.
import settings from '../../config/colloquial-display.json'

// Headings, or none: a list is headed by its categories only when every category has this many
// words. One heading over two words beside one over twenty is clutter, so then the list is one run.
const MIN_UNDER_HEADING = settings['least-under-heading']

// Rows under their category heading, in the order written ([heading, rows] pairs); one unheaded run
// ('' as its heading) when any category is too small, or when the rows have no categories.
export function grouped(rows) {
  if (!rows.length) return []
  const by = new Map()
  for (const r of rows) by.set(r.category ?? '', [...(by.get(r.category ?? '') ?? []), r])
  const headed = by.size > 1 && [...by].every(([heading, group]) => heading && group.length >= MIN_UNDER_HEADING)
  return headed ? [...by] : [['', rows]]
}

// A topic's words split into the ones it teaches new and the ones an earlier topic taught (`met`,
// marked by the loader from the course order), so no word is taught as new twice.
export const splitMet = (words) => [words.filter((w) => !w.met), words.filter((w) => w.met)]
