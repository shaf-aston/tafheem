/**
 * The glossary of the science as a tree the Map's chart can draw, pure data.
 *
 * Built here in the shape lib/pbsLayout and shell/PbsChart take (root, branches with a hue `c`, kids as
 * [arabic, english, tappable] triples), and never through lib/pbsTree's chartTree: its DEEP/SUB keys belong to
 * the Map's sciences and would graft their sub-topics onto these. Every box is tappable (a third `true`), since
 * a tap on a term opens its card; the chart is two levels, so a term's own kids show only in `branchChart`.
 */
import { layoutChart } from '../pbsLayout'
import { HUE } from '../pbsData'

const HUES = Object.values(HUE)
const ROOT = { ar: 'مصطلح الحديث', en: 'Hadith terms' }

// [arabic, english, tappable, leaf]: a tap opens the term's card, so no › drill hint (shell/PbsChart).
const pair = (t) => [t.arabic, t.en, true, true]

/** The whole tree: the hadith terms at its root, a group to a branch, its terms to the branch's kids. */
export function termsChart(glossary) {
  return {
    root: ROOT,
    branches: glossary.map((g, i) => ({ ar: g.name, en: g.title, c: HUES[i % HUES.length], hasKids: true, kids: g.terms.map(pair) })),
    footnote: [],
  }
}

/** One group alone: the group at the root, its terms the branches, each with the terms under it. */
export function branchChart(glossary, groupIndex) {
  const group = glossary[groupIndex]
  const c = HUES[groupIndex % HUES.length]
  return {
    root: { ar: group.name, en: group.title },
    branches: group.terms.map((t) => ({ ar: t.arabic, en: t.en, c, hasKids: true, leaf: true, kids: (t.kids ?? []).map(pair) })),
    footnote: [],
  }
}

/** { term, group } for the term named in Arabic, kids included, or null. */
export function termAt(glossary, arabic) {
  const find = (terms) => {
    for (const t of terms) {
      if (t.arabic === arabic) return t
      const inner = find(t.kids ?? [])
      if (inner) return inner
    }
    return null
  }
  for (const group of glossary) {
    const term = find(group.terms)
    if (term) return { term, group }
  }
  return null
}

/** The smallest label PbsChart draws, in px (the English sub-label of a term box). */
export const SMALLEST_LABEL = 9.5
/** The smallest the chart is drawn, as a share of its own width: its smallest label stays at 12px or more. */
export const MIN_SCALE = 12 / SMALLEST_LABEL
/** The page width, in px, from which the whole tree draws at MIN_SCALE without scrolling sideways. */
export const wholeWidth = (config) => Math.ceil(layoutChart(config).width * MIN_SCALE)
