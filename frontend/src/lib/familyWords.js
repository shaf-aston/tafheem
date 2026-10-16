/**
 * A telling's matn words (split by the server, the one place it is split) as runs: the words the build marked
 * (usul.db family_word) each on their own, the words between them joined. `marks` index `words`. Pure.
 */
export function markedRuns(words, marks) {
  const at = new Map(marks.map((m) => [m.at, m]))
  const runs = []
  let plain = []
  const flush = () => {
    if (plain.length) runs.push({ text: plain.join(' ') })
    plain = []
  }
  words.forEach((word, i) => {
    const mark = at.get(i)
    if (!mark) return plain.push(word)
    flush()
    runs.push({ text: word, kind: mark.kind, other: mark.other })
  })
  flush()
  return runs
}
