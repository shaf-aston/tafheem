/**
 * What a typed line means, and where it should go.
 *
 * One reader for both command surfaces: the bar in the header and the orbit
 * launcher behind the pen. Neither of them decides anything about routing, they
 * only draw what this returns, so the two can never disagree about what "@قول"
 * or "2:255" does.
 *
 * Pure on purpose. No fetch, no React, no clock. Every row it returns is just a
 * tab id and the value to hand that tab, which is exactly what App's switchTab
 * already takes, so nothing new had to be invented to carry a query across.
 */

import { isArabic } from './arabicText'

/** "2:255", with the Arabic comma allowed because a keyboard left in Arabic types it. */
const AYAH = /^\s*(\d{1,3})\s*[:٬،,]\s*(\d{1,3})\s*$/


const SURAHS = 114

/**
 * The id of one drawn row, given the surface's short name and the row's place
 * in the list. Focus stays in the typing box while the arrows walk the rows, so
 * the box has to name the current row by id for a screen reader to announce it.
 * Position, never the row's own key: that carries spaces and Arabic.
 */
export const rowId = (name, index) => `${name}-row-${index}`

/** The four groups, in the order they are shown. */
export const GROUPS = { ayah: 'Open ayah', go: 'Go to', dict: 'Dictionary', ask: 'Analyse' }

const clean = (text) => (text ?? '').trim()

/** Does this tab answer to what was typed: its id, its English name, or its Arabic one. */
function tabMatches(tab, term) {
  if (!term) return true
  const lower = term.toLowerCase()
  return (
    tab.id.includes(lower) ||
    tab.label.toLowerCase().includes(lower) ||
    tab.short.toLowerCase().includes(lower) ||
    tab.arabic.includes(term)
  )
}

/**
 * The rest of a tab name the reader has started typing, or '' when nothing is
 * being completed. This is the ghost the bar prints ahead of the cursor and Tab
 * accepts; it never completes a lookup, only a name, because a half-typed root
 * is a real root and guessing past it would be wrong.
 */
export function ghostFor(query, tabs) {
  const raw = clean(query)
  if (!raw || raw.startsWith('@') || AYAH.test(raw)) return ''
  const bare = raw.startsWith('/') ? raw.slice(1) : raw
  if (!bare || isArabic(bare)) return ''
  const lower = bare.toLowerCase()
  const hit = tabs.find((tab) => tab.label.toLowerCase().startsWith(lower) && tab.label.length > bare.length)
  return hit ? hit.label.slice(bare.length) : ''
}

/**
 * Every place a typed line could go, best first.
 *
 * The last row is always something that works. A line that matches no tab and
 * no address still gets sent somewhere that will read it, so the bar can never
 * answer with nothing while the reader watches.
 */
export function classify(query, tabs) {
  const raw = clean(query)
  if (!raw) return []

  const rows = []
  const add = (group, tabId, value, label, hint, arabic) =>
    rows.push({ key: `${group}:${tabId}:${value}`, group, tabId, value, label, hint, arabic })

  const ayah = AYAH.exec(raw)
  if (ayah && Number(ayah[1]) >= 1 && Number(ayah[1]) <= SURAHS) {
    const ref = `${Number(ayah[1])}:${Number(ayah[2])}`
    add(GROUPS.ayah, 'quran', ref, ref, 'Word by word, with the reason')
    return rows
  }

  // "@" is the one prefix that means a thing rather than a place: look this
  // root up, do not go looking for a tab called it.
  if (raw.startsWith('@')) {
    const root = clean(raw.slice(1))
    if (root) {
      add(GROUPS.dict, 'dict', root, root, "Ibn Faris's origin sense", true)
      add(GROUPS.dict, 'sarf', root, root, 'Every form of this word', true)
      add(GROUPS.dict, 'quran', root, root, 'Where it occurs in the Qur’an', true)
    }
    return rows
  }

  const slashed = raw.startsWith('/')
  const term = slashed ? clean(raw.slice(1)) : raw

  for (const tab of tabs) {
    if (tabMatches(tab, term)) add(GROUPS.go, tab.id, null, tab.label, tab.blurb ?? '', false)
  }

  // "/" was a promise to name a tab. Honour it literally rather than quietly
  // turning a mistyped tab name into a dictionary search.
  if (slashed) return rows

  if (isArabic(term)) {
    const oneWord = !term.includes(' ')
    if (oneWord) {
      add(GROUPS.dict, 'dict', term, term, 'Look this word up', true)
      add(GROUPS.dict, 'sarf', term, term, 'Break it into its pattern', true)
    }
    add(GROUPS.ask, 'nahw', term, term, 'Analyse it, word by word', true)
    return rows
  }

  add(GROUPS.ask, 'nahw', term, term, 'Send it to the analyser')
  return rows
}

/** The groups present in a result set, in display order, each with its rows. */
export function grouped(rows) {
  const order = [GROUPS.ayah, GROUPS.go, GROUPS.dict, GROUPS.ask]
  return order
    .map((group) => ({ group, rows: rows.filter((row) => row.group === group) }))
    .filter((block) => block.rows.length > 0)
}
