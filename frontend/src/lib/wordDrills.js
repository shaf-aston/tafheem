/**
 * A topic's word list turned into a quiz, so words need no exercises written by
 * hand. Each word gets one drill and the kinds take turns, easiest first:
 *   pick    see the English, pick the Arabic
 *   listen  hear the Arabic, pick it
 *   write   see the English, write the Arabic (or how it sounds)
 * Every drill is an ordinary exercise of a type the registry already draws, so
 * ExerciseHost and Practice host them unchanged. Pure and deterministic: the
 * same words always make the same quiz, and a rerender reshuffles nothing.
 */
const KINDS = ['pick', 'listen', 'write']
const OPTIONS = 4

// The answer among up to three other words, at a place that moves with the word.
function optionsFor(words, i) {
  const others = words.filter((_, j) => j !== i).map((w) => w.arabic)
  const picked = others.slice(i % Math.max(others.length, 1)).concat(others).slice(0, OPTIONS - 1)
  const options = [...new Set(picked)]
  options.splice(i % (options.length + 1), 0, words[i].arabic)
  return options
}

function drillOf(word, i, words, prefix) {
  const kind = words.length < 2 ? 'write' : KINDS[i % KINDS.length]
  const id = `${prefix}.word.${i + 1}.${kind}`
  if (kind === 'write') {
    return {
      id, type: 'translate_to_arabic', prompt: `Write “${word.english}” in Arabic, or how it sounds.`,
      answer: word.arabic, accepted: [word.arabic, word.transliteration],
    }
  }
  const prompt = kind === 'pick' ? `Which one is “${word.english}”?` : 'Which word did you hear?'
  return { id, type: 'choose', prompt, answer: word.arabic, options: optionsFor(words, i), ...(kind === 'listen' && { say: word.arabic }) }
}

export const wordDrills = (words, prefix) => words.map((w, i) => drillOf(w, i, words, prefix))
