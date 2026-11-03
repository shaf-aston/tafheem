import { arabicRuns } from '../../../lib/dictionary/laneEntry'

/**
 * Text whose Arabic runs arrive fenced in bidi marks (Lane's dump), drawn with
 * each run in its own <bdi> instead. The <bdi> keeps an Arabic word from
 * dragging the English punctuation round it, which is all the marks were for,
 * and unlike the marks it is never copied out as two invisible characters
 * around every Arabic word.
 */
export default function Fenced({ text }) {
  return arabicRuns(text).map((run, i) => (run.arabic ? <bdi key={i} lang="ar">{run.text}</bdi> : run.text))
}
