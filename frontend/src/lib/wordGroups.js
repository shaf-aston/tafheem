// Words under their category headings, shared by the word bank and a topic's word grid.
import settings from '../colloquial.json'

// A heading needs this many words in the list; a word whose category has fewer joins the heading before it.
const MIN_UNDER_HEADING = settings['least-under-heading']

// Rows under their category heading, in the order written; uncategorised rows sit under none.
export function grouped(rows) {
  const size = new Map()
  for (const r of rows) size.set(r.category ?? '', (size.get(r.category ?? '') ?? 0) + 1)
  const by = new Map()
  let heading = ''
  for (const r of rows) {
    const own = r.category ?? ''
    heading = size.get(own) < MIN_UNDER_HEADING && heading ? heading : own
    by.set(heading, [...(by.get(heading) ?? []), r])
  }
  return [...by]
}
