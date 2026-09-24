/**
 * The list of asbab al-nuzul reports, grouped and filtered.
 *
 * One event can carry four hundred reports (everything revealed at Madinah that
 * names no single event), so the panel needs a shape rather than a scroll: the
 * reports are grouped by surah in mushaf order, and past a knob's worth of them
 * a search box narrows the list.
 *
 * Pure: reports in, reports out. No React, no fetching.
 */
import settings from '../timelines.json'

const { asbab: ASBAB } = settings

/** Reports grouped by surah, in mushaf order, each group in ayah order. */
export function bySurah(reports) {
  const groups = new Map()
  for (const report of reports ?? []) {
    if (!groups.has(report.surah)) {
      groups.set(report.surah, { surah: report.surah, name: report.surah_name, reports: [] })
    }
    groups.get(report.surah).reports.push(report)
  }
  return [...groups.values()]
    .sort((a, b) => a.surah - b.surah)
    .map((group) => ({ ...group, reports: [...group.reports].sort((a, b) => a.ayah - b.ayah) }))
}

/**
 * The reports a typed query keeps. An address is matched as an address and never
 * as a prefix: "2:3" is the third ayah and must not answer with the thirtieth,
 * and "2" is the whole of al-Baqarah and not surahs 20 to 29. Anything else
 * matches the surah's name or the report's own words, so "Badr" finds the report
 * that tells it whatever surah it is in.
 */
const ADDRESS = /^(\d+)(:(\d+)?)?$/

export function matching(reports, query) {
  const wanted = String(query ?? '').trim().toLowerCase()
  if (!wanted) return reports ?? []
  const address = ADDRESS.exec(wanted)
  if (address) {
    const [, surah, colon, ayah] = address
    return (reports ?? []).filter((report) => (
      String(report.surah) === surah && (!colon || !ayah || String(report.ayah) === ayah)
    ))
  }
  return (reports ?? []).filter((report) => (
    report.surah_name.toLowerCase().includes(wanted)
    || report.opening.toLowerCase().includes(wanted)
  ))
}

/**
 * The ayah words a report opens on, for its one line in the list. The book opens
 * each as `Concerning Allah's words "…": who narrated it…`; the chain belongs to
 * the opened report, not the list. An opening in any other shape is kept whole.
 */
// Either quote mark, closed by the same one with no letter after it, so an
// apostrophe inside the words ("it's") does not end them.
export const quotedWords = (opening) => /words\s+(["'])(.+?)\1(?!\p{L})/u.exec(opening ?? '')?.[2] ?? (opening ?? '')

/** Whether a list this long is worth a search box. */
export const needsSearch = (count) => count >= ASBAB['search-from']

/**
 * A passage split back into the reports the book gives on that one ayah.
 *
 * Several reports on one ayah are stored as one passage with "[1 / 3]" markers,
 * because the library holds one passage per ayah. They are shown as the three
 * the book actually gives, never silently reduced to the first.
 */
export function reportsIn(text) {
  const marked = String(text ?? '').split(/\[\d+ \/ \d+\]\s*/).map((part) => part.trim()).filter(Boolean)
  return marked.length ? marked : []
}
