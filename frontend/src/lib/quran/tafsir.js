/**
 * A tafsir commonly comments on a run of ayahs in one passage rather than on
 * one ayah at a time. This names the run, so a reader handed four paragraphs
 * about ten ayahs is told that rather than reading it as four paragraphs about
 * the one they clicked.
 */

/** "2:255", or "78:1–10" where one passage was written about a run. */
export function passageLabel(surah, covers) {
  if (!covers?.length) return ''
  const first = covers[0]
  const last = covers[covers.length - 1]
  return first === last ? `${surah}:${first}` : `${surah}:${first}–${last}`
}
