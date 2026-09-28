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
import { narrated, saying } from '../../lib/hadithWords'
import { themeVariable } from '../../theme'

const TONE = {
  said: { color: 'var(--hadith-said)' },
  told: { color: 'var(--hadith-told)' },
  plain: { color: 'var(--text-dim)' },
}
// How much of one hadith shows before the rest waits behind a press.
const LINES = Number(themeVariable('--hadith-lines')) || 7

/** One run of words, each span wearing the colour of whoever is talking. */
function Spans({ text, marks }) {
  return saying(text).map((span, i) => (
    <span key={`${span.kind}-${i}`} style={TONE[span.kind]}>
      {span.kind === 'said' ? `${marks[0]}${span.text}${marks[1]}` : span.text}{' '}
    </span>
  ))
}

/** `action` is a slot beside the number: a favorite star or a collection badge. */
export default function HadithText({ label, arabic, english = '', accent, action = null, className = '' }) {
  const { narrator, body } = narrated(english)

  return (
    <li className={`rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 ${className}`.trim()}>
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
          <Spans text={arabic} marks={['«', '»']} />
        </ArabicText>

        {english && (
          <p className="type-ui leading-relaxed mt-3 pt-3 border-t border-[var(--border)]">
            {narrator && <span style={TONE.told}>{narrator} </span>}
            <Spans text={body} marks={['“', '”']} />
          </p>
        )}
      </ShowRest>
    </li>
  )
}
