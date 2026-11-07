/**
 * The Map's content: nine Islamic sciences as product-breakdown trees, root to
 * leaf topic. Each science is one nested file in ./pbs (named by its id),
 * built and checked science by science against the classical curricula named
 * in its `frame`. This module only loads them and colours them.
 *
 * File shape: `{ id, ar, en, frame, hue, footnote, root, branches }`. `hue` is
 * the science's card colour on the Map index. `branches` are its book-level
 * divisions (never أبواب inside one; each footnote states the rule it follows
 * and what it leaves out). Every node is `{ ar, en, kids? }`; a branch also
 * names its `hue`, and every box below it inherits that colour.
 *
 * `CHARTS`: one entry per science with `accent` (its index colour), `footnote`
 * and `tree`, whose nodes each carry their colour `c`.
 */

import { colorFor } from "../../theme"

/** Each branch colour once, toned per look: line, box wash, label, from theme.json's `pbs` group. A chart names one by key. */
const mix = (hue, wash) => `color-mix(in oklch, ${colorFor("pbs", hue)} ${colorFor("pbs", wash)}, var(--surface))`
export const HUE = Object.fromEntries(
  ["teal", "rose", "amber", "violet", "indigo", "slate", "sky", "slateDeep", "blue", "emerald", "orange", "cyan"].map((hue) => [hue, {
    bar: colorFor("pbs", hue),
    head: mix(hue, "head-wash"),
    fill: mix(hue, "wash"),
  }]),
)

const coloured = (node, c) => ({ ar: node.ar, en: node.en, c, kids: (node.kids ?? []).map((kid) => coloured(kid, c)) })

function chartOf({ hue, root, branches, ...rest }) {
  return {
    ...rest,
    accent: HUE[hue].bar,
    tree: { ar: root.ar, en: root.en, kids: branches.map((b) => coloured(b, HUE[b.hue])) },
  }
}

const files = import.meta.glob("./pbs/*.json", { eager: true, import: "default" })

/** Sorted by id: the Map numbers the sciences 1 to 9 by how they lead into each other, in threes that belong together (the law, the sources, the language), and its arrow keys walk this order. */
export const CHARTS = Object.keys(files).sort().map((path) => chartOf(files[path]))
