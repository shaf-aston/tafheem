/**
 * Where a WheelPicker spins to for what was typed. A number jumps to that
 * option's value; letters jump to the first option with a word that starts
 * with them, so "nis" and "an" both land on An-Nisa, never on a word's middle.
 * Case, hyphens and apostrophes are ignored.
 */
const fold = (text) => String(text).toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '')

const words = (text) => fold(text).split(/[^\p{L}\p{N}]+/u).filter(Boolean)

/** The index of the matching option, or -1 when nothing matches. */
export function wheelFind(options, typed) {
  const query = fold(typed).replace(/[^\p{L}\p{N}]+/gu, '')
  if (!query) return -1
  if (/^\d+$/.test(query)) return options.findIndex((o) => String(o.value) === String(Number(query)))
  return options.findIndex((o) =>
    [o.label, ...(o.keys ?? [])].some((text) =>
      words(text).join('').startsWith(query) || words(text).some((w) => w.startsWith(query))))
}
