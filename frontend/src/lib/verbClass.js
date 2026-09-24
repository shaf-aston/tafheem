/**
 * Split the verb class into the name and what the name means.
 *
 * It arrives as one string, "صحيح سالم: no weak letter, no hamzah, no repeat":
 * the name the books use, then the explanation. They are two different things, so
 * the card shows them as two and the mark between them never reaches the screen.
 *
 * A class with no Arabic name passes straight through: an AI answer, or a
 * preset's "Form II". Better a plain label than a wrong split.
 *
 * Lives here rather than in the panel because it is a regex over a handful of
 * interchangeable marks and a range of Arabic letters, exactly the kind of
 * thing that stops matching without anything looking broken.
 */

// An Arabic name, then a colon, en-dash, em-dash or hyphen, then the rest. The
// app's own data uses the colon; the older marks stay accepted because a preset
// or an AI answer can still arrive written either way. `s` so an explanation
// that wraps onto another line still belongs to the same class.
const CLASS_NAME = /^([؀-ۿ\s]+?)\s*[:–—-]\s*(.+)$/s

export function verbClass(text) {
  const named = text && CLASS_NAME.exec(text)
  return named
    ? { value: named[1], gloss: named[2], arabic: true }
    : { value: text }
}
