/**
 * One hadith's own words: Arabic and English, said drawn apart from told.
 *
 * Promoted out of TimelineHadith, which drew this the same way for the
 * hadiths a timeline event cites; the Hadith tab's browse and search both
 * need the identical rendering for a hadith found a different way. One
 * implementation, not two that would drift the moment either was touched.
 *
 * The chain of narrators, the scene, who did what next: all of that is the
 * telling, drawn back so the eye lands on the saying. The books mark the
 * saying themselves with quote marks and lib/hadithWords reads that mark;
 * where a book marked nothing, nothing is claimed and the hadith prints in
 * one plain colour. The marks are kept as well as the colour, because a
 * reader who cannot tell two colours apart still has to be able to tell
 * speech from telling.
 */
import ArabicText from './ArabicText'
import ShowRest from './ShowRest'
import { MARKS, narrated, saying } from '../../lib/hadithWords'
import { runs, told, withoutMarks } from '../../lib/rijal'
import { useFirstSight } from '../../lib/firstSight'
import { themeVariable } from '../../theme'

const TONE = {
  said: { color: 'var(--hadith-said)' },
  told: { color: 'var(--hadith-told)' },
  plain: { color: 'var(--text-dim)' },
}
// How much of one hadith shows before the rest waits behind a press.
const LINES = Number(themeVariable('--hadith-lines')) || 7
// Cards past this many appear together, so a long book never waits on its own stagger.
const STAGGER_CAP = Number(themeVariable('--hadith-stagger-cap')) || 8

/**
 * One run of words, each span wearing the colour of whoever is talking.
 * `names` are [start, end, id] slices of `text`; each becomes a button
 * that calls `onNarrator(id)`.
 */
function Spans({ text, marks, names = [], onNarrator }) {
  // saying() drops the direction marks, so the slices move with them.
  const at = withoutMarks(text, names)
  const clean = text.replace(MARKS, '')
  let cursor = 0
  return saying(clean).map((span, i) => {
    const start = clean.indexOf(span.text, cursor)
    cursor = start + span.text.length
    const parts = runs(span.text, at, start).map((run, j) => run.id == null ? run.text : (
      <button
        key={j}
        type="button"
        onClick={() => onNarrator(run.id)}
        aria-label={`About ${run.text}`}
        className="press text-inherit underline underline-offset-4 decoration-dotted decoration-[var(--text-faint)] hover:decoration-[var(--text-dim)]"
      >
        {run.text}
      </button>
    ))
    return (
      <span key={`${span.kind}-${i}`} style={TONE[span.kind]}>
        {span.kind === 'said' ? <>{marks[0]}{parts}{marks[1]}</> : parts}{' '}
      </span>
    )
  })
}

/**
 * `action` is a slot beside the number: a favorite star or a collection badge.
 * `hideChain` drops the chain of narrators but the one who tells the hadith:
 * lib/rijal told finds where the chain ends. The English
 * "Narrated X:" line already names only that one, so it stays.
 * `names` are the narrators named in the Arabic (lib/rijal); with the chain
 * hidden, the teller and anyone named after him keep theirs.
 * `footer` sits under the text: the other narrations of this number.
 */
export default function HadithText({ label, arabic, english = '', accent, action = null, id, index = 0, className = '', hideChain = false, names = [], onNarrator, footer = null }) {
  const { narrator, body } = narrated(english)
  const shown = hideChain ? told(arabic, names) : { text: arabic, names }
  const rise = useFirstSight(`hadith:${arabic.slice(0, 30)}`)

  return (
    <li
      id={id}
      style={{ '--i': Math.min(index, STAGGER_CAP) }}
      className={`${rise ? 'rise-in ' : ''}rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 scroll-mt-[calc(var(--app-header-h,0px)+6rem)] ${className}`.trim()}
    >
      <div className="flex items-center justify-between gap-2 mb-3">
        <span
          style={{ color: accent, borderColor: accent }}
          className="type-tiny tabular-nums min-w-7 h-7 px-2 grid place-items-center rounded-full border"
        >
          {label}
        </span>
        {action}
      </div>

      <ShowRest lines={LINES} accent={accent} more="Show the rest" less="Show less">
        <ArabicText as="p" size="base" className="block leading-loose m-0">
          <Spans text={shown.text} marks={['«', '»']} names={shown.names} onNarrator={onNarrator} />
        </ArabicText>

        {english && (
          <p className="type-ui leading-relaxed mt-3 pt-3 border-t border-[var(--border)]">
            {narrator && <span style={TONE.told}>{narrator} </span>}
            <Spans text={body} marks={['“', '”']} />
          </p>
        )}
      </ShowRest>
      {footer}
    </li>
  )
}
