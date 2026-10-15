/**
 * Render an I'raab analysis result as plain text suitable for the clipboard.
 * Terms print in Arabic, as on the page: مرفوع, not "raf'".
 */
import { caseLabel } from './grammarTerms'
import { kids, pieces } from './tarkeebLayout'

const GAP = '؟'

// The columns a node covers, in reading order (children come sorted).
const span = (node) => (node.word != null ? [node.word] : (kids(node) ?? []).flatMap(span))
const named = (piece) => piece.role && (piece.detail ? `${piece.role} (${piece.detail})` : piece.role)
// What the diagram writes for a node: the unit's name, then its job, then the
// pieces inside one word (a verb and its hidden doer).
const said = (node) =>
  [node.label, pieces(node)?.map(named).filter(Boolean).join(' + ') ?? named(node)].filter(Boolean).join(': ') || GAP

/** The diagram as text: one line per word or joined unit, outermost first. The
    pieces of one written word print joined (فَسَوَّىٰهُنَّ), as it is written. */
function structureLines({ words, written }, node, depth = 0) {
  const cols = span(node)
  const text = cols.map((i, k) => (k && written && written[i] === written[cols[k - 1]] ? '' : ' ') + words[i]).join('').trim()
  return [`${'  '.repeat(depth)}${text} = ${said(node)}`, ...(kids(node) ?? []).flatMap((kid) => structureLines({ words, written }, kid, depth + 1))]
}

export function buildIraabExportText(data) {
  const lines = [`I'raab Analysis: ${data.sentence}`]
  if (data.summary) lines.push(`Sentence type: ${data.summary}`)
  lines.push('')

  for (const w of data.words) {
    lines.push(w.word)
    if (w.role) lines.push(`  Role: ${w.role}`)
    if (w.case) lines.push(`  Case: ${caseLabel(w.case)}${w.sign ? ` (${w.sign})` : ''}`)
    if (w.root) lines.push(`  Root: ${w.root}`)
    if (w.reason) lines.push(`  Reason: ${w.reason}`)
    if (w.book) lines.push(`  Book: ${w.book}`)
    lines.push('')
  }
  if (data.tree?.tree) lines.push('Structure:', ...structureLines(data.tree, data.tree.tree))
  return lines.join('\n')
}
