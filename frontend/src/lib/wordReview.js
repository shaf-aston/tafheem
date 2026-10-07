/**
 * Which of a topic's words to review now, from the progress store's summary of
 * the words module. The schedule itself (FSRS, on the server) decides when a word
 * is due; this only sorts a topic's words by it:
 *   due    answered before and due again now: the ones about to be forgotten
 *   fresh  never answered: next, so a topic is learnt as well as kept
 *   later  answered and not due yet: left alone, only counted
 * Pure, so the order is testable without a server.
 */
import { wordKey } from './wordDrills'

export const SESSION = 10

export function reviewOf(words, rows, dialect) {
  const byItem = new Map(rows.map((r) => [r.item, r]))
  const due = [], fresh = [], later = []
  for (const w of words) {
    const row = byItem.get(wordKey(dialect, w))
    if (!row) fresh.push(w)
    else (row.due ? due : later).push({ word: w, at: row.dueAt })
  }
  due.sort((a, b) => (a.at ?? '').localeCompare(b.at ?? ''))
  const next = later.map((l) => l.at).filter(Boolean).sort()[0] ?? null
  return {
    session: [...due.map((d) => d.word), ...fresh].slice(0, SESSION),
    due: due.length,
    fresh: fresh.length,
    later: later.length,
    next,
  }
}
