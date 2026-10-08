/**
 * A telling's matn as runs: the words the build marked (usul.db family_word) each on their own, the words between
 * them joined. `marks` index the matn split on whitespace. Pure.
 */
export function markedRuns(matn, marks) {
  const at = new Map(marks.map((m) => [m.at, m]))
  const runs = []
  let plain = []
  const flush = () => {
    if (plain.length) runs.push({ text: plain.join(' ') })
    plain = []
  }
  matn.split(/\s+/).filter(Boolean).forEach((word, i) => {
    const mark = at.get(i)
    if (!mark) return plain.push(word)
    flush()
    runs.push({ text: word, kind: mark.kind, other: mark.other })
  })
  flush()
  return runs
}
