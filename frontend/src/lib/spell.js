/**
 * A word said slowly, piece by piece, then whole: قَطَاة → "قَ، طَا، ةْ، قَطَاة".
 *
 * A piece is a letter with its marks, and a bare long vowel (ا و ي ى) joins the
 * piece before it, since alone it has no sound of its own (طَا, not طَ then ا).
 * The Arabic comma is a pause every voice keeps, so this is one phrase to the
 * server, made and cached like any other. A bare last letter gets a sukun, so
 * the voice says it instead of trailing off (the ة the reader could not hear).
 */
const MARK = /[ً-ْٰ]/
const LONG = new Set(['ا', 'و', 'ي', 'ى'])
const SUKUN = 'ْ'
const PAUSE = '، '

/** The pieces of `word`, each a letter and its marks. */
export function pieces(word) {
  const out = []
  for (const ch of word.replace(/\s+/g, '')) {
    if (MARK.test(ch) && out.length) out[out.length - 1] += ch
    else if (LONG.has(ch) && out.length && MARK.test(out.at(-1).at(-1)) && !out.at(-1).endsWith(SUKUN)) out[out.length - 1] += ch
    else out.push(ch)
  }
  if (out.length && !MARK.test(out.at(-1).at(-1)) && !LONG.has(out.at(-1).at(-1))) out[out.length - 1] += SUKUN
  return out
}

/** What a letter-by-letter button says: the pieces, then the word. */
export const spelled = (word) => [...pieces(word), word.trim()].join(PAUSE)
