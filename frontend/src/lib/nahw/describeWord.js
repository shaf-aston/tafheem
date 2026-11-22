/**
 * Everything the page says about one analysed word, worked out in one place, so the
 * grid, the table, the peek, the card and the copied text cannot drift apart.
 *
 * `words` is the sentence the word sits in; it is only needed for the head word.
 */
import { caseFrom, caseGloss, caseLabel, isUnnamed, reading, roleGloss } from './grammarTerms'
import { roleVar } from './roleColors'

export function describeWord(word, words = []) {
  const headIndex = caseFrom(word)
  const head = headIndex === undefined ? null : words[headIndex] ?? null
  return {
    // the term the word is called by: its fuller name when the analyser gives one
    label: word.name ?? word.role,
    hasRole: Boolean(word.role),
    unnamed: isUnnamed(word),
    roleGloss: roleGloss(word.name) || roleGloss(word.role),
    color: roleVar(word.role_key),
    caseText: word.case ? caseLabel(word.case) : '',
    caseGloss: caseGloss(word.case),
    // case and sign as one reading (grammarTerms.reading), the pieces in order
    reading: reading(word),
    headIndex,
    head,
    // true when the word only copies its head's case (a تابع), not governed by it
    follows: headIndex !== undefined && word.governor == null,
  }
}
