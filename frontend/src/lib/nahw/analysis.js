/**
 * One shape for an analysed sentence, whichever source it came from, so the
 * pages that draw one never reshape a raw response themselves:
 *
 *   { sentence, words, tree, summary, source, unvowelled }
 *
 * - sentence:   the text as one string ('' when unknown)
 * - words:      the per-word records, as the source sent them ([] when none);
 *               per-word facts are lib/nahw/describeWord's job, not this one's
 * - tree:       the tarkeeb chart ({ words, written, tree, coverage, source }) or null
 * - summary:    the sentence's type in a line, or null
 * - source:     where the words came from (a provenance record), or null
 * - unvowelled: { ar, en } note for a sentence typed bare, or null
 *
 * The two sources still differ in their word records, and that is kept, not
 * hidden: an /analyze word names itself `word`, an ayah-store word `arabic`
 * and carries its corpus `position` (see wordKey).
 */

/** The common shape from parts; anything missing gets its empty value. */
export function toAnalysis({ sentence, words, tree, summary, source, unvowelled } = {}) {
  return {
    sentence: sentence ?? '',
    words: Array.isArray(words) ? words : [],
    tree: tree ?? null,
    summary: summary ?? null,
    source: source ?? null,
    unvowelled: unvowelled ?? null,
  }
}

/** The backend `/analyze` (i'raab) response. Its `parse` and `read_failed` are not read by any page. */
export const fromAnalyzeResponse = (json) => toAnalysis(json ?? {})

/**
 * One ayah from the ayah store: `ayah` is the `/quran/{s}/{a}` record (words,
 * arabic_text, source), `tarkeeb` the `/quran/{s}/{a}/tarkeeb` chart. They are
 * separate requests, so either may be absent. The ayah has no summary and is
 * never typed unvowelled. Its `source` is the corpus the words came from; the
 * chart's own source (treebank or nahw) stays on `tree.source`.
 */
export function fromAyahStore({ ayah, tarkeeb } = {}) {
  const words = ayah?.words ?? []
  return toAnalysis({
    // The words joined, as the server builds arabic_text; the record's line only when no words came.
    sentence: words.length ? words.map((w) => w.arabic).join(' ') : ayah?.arabic_text,
    words,
    tree: tarkeeb,
    source: ayah?.source,
  })
}

/** The key an ayah-store word is known by: its corpus `position`, else its index. */
export const wordKey = (word, i) => word.position || i
