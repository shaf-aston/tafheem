/**
 * The compact tarkeeb: every word's own name straight under (or beside) it, and each
 * join as one brace on the row of its depth. No thread runs from a word down to a name
 * rows away, so the chart is only as tall (or, turned on its side, as wide) as the
 * sentence is deep.
 *
 * Pure: no DOM, no React.
 */
import { GAP, flat, kids, measure, pieces, runs } from './tarkeebLayout'

const named = (piece) => piece.role || piece.gap

/** A leaf's names: its pieces' when it has them (فعل · فاعل · مفعول به), else its own. */
function leafNames(leaf) {
  const list = pieces(leaf) ?? [leaf]
  return list.filter(named).map((p) => ({ role: p.gap ? GAP : p.role, tone: p.gap ? 'gap' : p.tone, pronoun: p.pronoun, detail: p.detail }))
}

/**
 * { columns, spans, groups, depth }
 * columns[i]: { word, hidden, names: [{ role, tone, pronoun }] } per piece
 * spans: the written words, [{ from, to, text, nth, hidden }]
 * groups: [{ id, from, to, level, role, label, tone }] (level 1 = the joins nearest the words)
 */
export function compact({ words, written, tree }) {
  const columns = words.map((word) => ({ word, hidden: false, names: [] }))
  const groups = []
  const walk = (node, depth) => {
    if (kids(node)) {
      groups.push({ id: groups.length, from: node.from, to: node.to, level: node.level, role: node.role, label: node.label, tone: node.tone, depth })
      kids(node).forEach((kid) => walk(kid, depth + 1))
      return
    }
    const column = columns[node.word]
    if (!column) return
    column.hidden = !!node.hidden
    column.tone = node.gap ? 'gap' : node.tone
    // a word whose pieces make up another job (خبر = حرف جر + مجرور): the pieces under it, the job on a brace of its own
    if (pieces(node) && !flat(node)) {
      column.names.push(...leafNames(node))
      groups.push({ id: groups.length, from: node.word, to: node.word, level: 1, role: node.role, label: node.label, tone: node.tone, depth })
    } else column.names.push(...leafNames(node))
  }
  const measured = measure(tree)
  walk(measured, 0)
  const all = runs(words, written)
  let nth = 0
  const spans = all.map(({ from, to }) => {
    const hidden = columns[from].hidden
    const span = { from, to, text: words.slice(from, to + 1).join('').replaceAll('ـ', ''), nth: hidden ? -1 : nth, hidden }
    if (!hidden) nth += 1
    return span
  })
  return { columns, spans, groups, depth: measured.level }
}

/** The words a group covers, read in order: for the panel's "this part of the sentence". */
export const groupText = (layout, group) =>
  layout.spans.filter((s) => s.from >= group.from && s.to <= group.to && !s.hidden).map((s) => s.text).join(' ')
