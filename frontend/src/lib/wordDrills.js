/**
 * A topic's word list turned into a quiz, so words need no exercises written by
 * hand. Each word gets one drill and the kinds take turns, easiest first:
 *   pick    see the English, pick the Arabic
 *   listen  hear the Arabic, pick it
 *   write   see the English, write the Arabic (or how it sounds)
 * Every drill is an ordinary exercise of a type the registry already draws, so
 * ExerciseHost and Practice host them unchanged. Pure and deterministic: the
 * same words always make the same quiz, and a rerender reshuffles nothing.
 *
 * Given a dialect, each drill is filed under the word itself (WORDS_MODULE,
 * wordKey), so the review schedule learns the word whichever drill or topic
 * asked it. `pool` is where the wrong options come from, when only some of a
 * topic's words are being asked.
 */
const KINDS = ['pick', 'listen', 'write']
const OPTIONS = 4

export const WORDS_MODULE = 'words'
export const wordKey = (dialect, word) => `${dialect}:${word.arabic}`

// The answer among up to three other words, at a place that moves with the word.
function optionsFor(pool, word, i) {
  const others = pool.map((w) => w.arabic).filter((a) => a !== word.arabic)
  const picked = others.slice(i % Math.max(others.length, 1)).concat(others).slice(0, OPTIONS - 1)
  const options = [...new Set(picked)]
  options.splice(i % (options.length + 1), 0, word.arabic)
  return options
}

function drillOf(word, i, pool, prefix, dialect) {
  const kind = pool.length < 2 ? 'write' : KINDS[i % KINDS.length]
  const base = { id: `${prefix}.word.${i + 1}.${kind}`, answer: word.arabic, ...(dialect && { progress: { module: WORDS_MODULE, item: wordKey(dialect, word) } }) }
  if (kind === 'write') {
    return { ...base, type: 'translate_to_arabic', prompt: `Write “${word.english}” in Arabic, or how it sounds.`, accepted: [word.arabic, word.transliteration] }
  }
  const prompt = kind === 'pick' ? `Which one is “${word.english}”?` : 'Which word did you hear?'
  return { ...base, type: 'choose', prompt, options: optionsFor(pool, word, i), ...(kind === 'listen' && { say: word.arabic }) }
}

export const wordDrills = (words, prefix, { pool = words, dialect } = {}) =>
  words.map((w, i) => drillOf(w, i, pool, prefix, dialect))
