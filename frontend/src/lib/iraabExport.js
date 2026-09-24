/**
 * Render an I'raab analysis result as plain text suitable for the clipboard.
 * Terms print in Arabic, as on the page: مرفوع, not "raf'".
 */
import { caseLabel, signLabel } from './grammarTerms'

export function buildIraabExportText(data) {
  const lines = [`I'raab Analysis: ${data.sentence}`]
  if (data.summary) lines.push(`Sentence type: ${data.summary}`)
  lines.push('')

  for (const w of data.words) {
    lines.push(w.word)
    if (w.role) lines.push(`  Role: ${w.role}`)
    if (w.case) lines.push(`  Case: ${caseLabel(w.case)}${w.sign ? ` (${signLabel(w.sign)})` : ''}`)
    if (w.root) lines.push(`  Root: ${w.root}`)
    if (w.reason) lines.push(`  Reason: ${w.reason}`)
    lines.push('')
  }
  return lines.join('\n')
}
