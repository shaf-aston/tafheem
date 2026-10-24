/**
 * Which tab a progress module belongs to. A module id is a tab's id, or one of the
 * names a tab files under (its `modules`), optionally with a meaning language
 * ("quiz:ur"). Home's cards and the profile's rows both read it from here.
 */
import { MEANINGS } from '../quiz/quiz'
import { TABS } from './tabs'

const parts = (module) => module.split(':')

/** The tab a module belongs to, or null for a name no tab claims. */
export function tabOf(module) {
  const [base] = parts(module)
  return TABS.find((tab) => tab.id === base || tab.modules?.includes(base)) ?? null
}

/** Words for a module row: "Quiz · Urdu", "Colloquial · words"; an unknown id shows as it is. */
export function labelOf(module) {
  const [base, language] = parts(module)
  const tab = tabOf(module)
  if (!tab) return module
  return [tab.label, base !== tab.id && base, language && (MEANINGS[language]?.name ?? language)]
    .filter(Boolean).join(' · ')
}

/** `{ [tabId]: { learnt, attempts, lastAt } }`, summed over each tab's modules. */
export function progressByTab(modules = []) {
  const sums = {}
  for (const row of modules) {
    const tab = tabOf(row.module)
    if (!tab) continue
    const sum = sums[tab.id] ??= { learnt: 0, attempts: 0, lastAt: null }
    sum.learnt += row.learnt
    sum.attempts += row.attempts
    if (row.lastAt && (!sum.lastAt || row.lastAt > sum.lastAt)) sum.lastAt = row.lastAt
  }
  return sums
}
