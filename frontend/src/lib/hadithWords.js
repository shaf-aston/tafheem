/**
 * A hadith split into who is talking: the words that were said, and the telling
 * around them.
 *
 * Reading a hadith as one grey block hides the thing a reader came for. What
 * the Prophet said, what a companion saw, what happened next and who passed it
 * on are four different kinds of sentence, and the books themselves mark the
 * first one: sunnah.com puts the said words between quote marks, in the Arabic
 * and in the English both.
 *
 * So the mark is read, never guessed. A quoted stretch is `said`; everything
 * outside it is `told` and is drawn back. Where a hadith carries no quote marks
 * at all (about one in six, mostly Muslim's English), nothing is claimed: the
 * whole of it comes back as one plain span and the reader sees it in one
 * colour, which is what it looked like before any of this.
 *
 * Pure: a string in, spans out. No React.
 */

// The books' own speech mark, with the direction marks sunnah.com sets around
// it. Those marks are invisible and would otherwise be printed inside the words.
const MARKS = /[‎‏]/g
const QUOTE = /["“”«»]/

/**
 * Who says what, in order. Every span is `said`, `told` or `plain`, and joining
 * their texts gives the hadith back unchanged apart from the direction marks.
 */
export function saying(text) {
  const clean = String(text ?? '').replace(MARKS, '')
  if (!clean.trim()) return []
  const pieces = clean.split(QUOTE)
  // One piece means no quote mark was found, so the books have not said which
  // part is speech and neither do we.
  if (pieces.length < 2) return [{ kind: 'plain', text: clean.trim() }]
  return pieces
    .map((piece, i) => ({ kind: i % 2 ? 'said' : 'told', text: piece.trim() }))
    .filter((span) => span.text)
}

// "Narrated Abu Huraira:", "It is narrated on the authority of X that ... said:"
// The books end the line that names the narrator with a colon and start the
// hadith after it, so that colon is the split rather than a guess at one.
const NARRATOR = /^([^:]{0,160}?:)\s*(.*)$/s

/** The English as two parts: who is telling it, and what they told. */
export function narrated(english) {
  const clean = String(english ?? '').replace(MARKS, '').trim()
  const match = NARRATOR.exec(clean)
  if (!match) return { narrator: '', body: clean }
  return { narrator: match[1].trim(), body: match[2].trim() }
}

/**
 * The key a reference looks up in the library's hadith map, and the name
 * sunnah.com prints for it: "muslim:157c". The letter is there when one
 * reference number covers several narrations and the event means one of them.
 */
export const hadithKey = (ref) => (ref?.hadith ? `${ref.hadith}:${ref.number}${ref.part ?? ''}` : '')

/**
 * Which hadiths each part of one event prints, so none is printed twice.
 *
 * One long hadith often tells a whole run: the fall of Constantinople and the
 * two steps inside it are all one narration, and printing it under the event
 * and again under each step is the same page of Arabic three times over. The
 * first place that cites it prints it; everything below says the number and
 * leaves the words to the copy above.
 *
 * Keyed by step id, with the event itself under the empty string.
 */
export function printedBy(event) {
  const seen = new Set()
  const byPart = new Map()
  const take = (id, refs) => {
    const keys = (refs ?? []).map(hadithKey).filter((key) => key && !seen.has(key))
    for (const key of keys) seen.add(key)
    byPart.set(id, new Set(keys))
  }
  const walk = (steps) => {
    for (const step of steps ?? []) {
      take(step.id, step.refs)
      walk(step.steps)
    }
  }
  take('', event?.refs)
  walk(event?.steps)
  return byPart
}
