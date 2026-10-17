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
 * saying themselves with quote marks; where they did not, the saying is read
 * from its verbs, and a hadith with no saying (what was done) is all body.
 * lib/hadithWords spoken owns that rule. The book's own marks are kept as well as the colour,
 * because a reader who cannot tell two colours apart still has to be able to
 * tell speech from telling.
 */
import ArabicText from './ArabicText'
import ShowRest from './ShowRest'
import { narrated, spoken } from '../../lib/hadithWords'
import { runs, told, withoutMarks } from '../../lib/rijal'

import NarratorLink from './NarratorLink'
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
 * The quote marks are the book's own, where the book put them; `arabic` only
 * draws a straight " as the « or » it stands for.
 * `names` are [start, end, id] slices of `text`; each is a ui/NarratorLink.
 * `from` (where the body starts) goes to lib/hadithWords spoken, which owns the colour rule.
 */
function Spans({ text, arabic = false, names = [], onNarrator, from = null }) {
  // saying() drops the direction marks, so the slices move with them.
  const at = withoutMarks(text, names)
  const mark = (ch, opens) => (arabic && ch === '"' ? (opens ? '«' : '»') : ch)
  let cursor = 0
  return spoken(text, { from }).map((span, i) => {
    const start = cursor + span.open.length
    cursor = start + span.text.length + span.close.length
    const parts = runs(span.text, at, start).map((run, j) => (
      <NarratorLink key={j} id={run.id} onOpen={onNarrator}>{run.text}</NarratorLink>
    ))
    return (
      <span key={`${span.kind}-${i}`} style={TONE[span.kind]}>
        {mark(span.open, true)}{parts}{mark(span.close, false)}
      </span>
    )
  })
}

/**
 * `action` is a slot beside the number: a favorite star or a collection badge.
 * `hideChain` drops the chain of narrators but the one who tells the hadith:
 * lib/rijal told finds where the chain ends, from `cut` (the server's [teller_at, body_at]). The English
 * "Narrated X:" line already names only that one, so it stays.
 * `names` are the narrators named in the Arabic (lib/rijal); with the chain
 * hidden, the teller and anyone named after him keep theirs.
 * `footer` sits under the text: the other narrations of this number.
 * `split` sets English left and Arabic right on a wide screen, as sunnah.com does; a phone stacks them.
 */
export default function HadithText({ label, arabic, cut = null, english = '', accent, action = null, id, index = 0, className = '', hideChain = false, split = false, names = [], onNarrator, footer = null }) {
  const { narrator, body } = narrated(english)
  const shown = hideChain ? told(arabic, cut, names) : { text: arabic, names }
  const from = cut ? Math.max(0, cut[1] - (arabic.length - shown.text.length)) : null

  return (
    <li
      id={id}
      style={{ '--i': Math.min(index, STAGGER_CAP) }}
      className={`rise-in rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 scroll-mt-[calc(var(--app-header-h,0px)+6rem)] ${className}`.trim()}
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
        <div className={split && english ? 'md:grid md:grid-cols-2 md:gap-x-8 md:items-start' : ''}>
        <ArabicText as="p" size="base" className="block leading-loose m-0">
          <Spans text={shown.text} arabic names={shown.names} onNarrator={onNarrator} from={from} />
        </ArabicText>

        {english && (
          <p className={`type-ui leading-relaxed mt-3 pt-3 border-t border-[var(--border)] ${split ? 'md:order-first md:m-0 md:p-0 md:border-t-0' : ''}`}>
            {narrator && <span style={TONE.told}>{narrator} </span>}
            <Spans text={body} from={0} />
          </p>
        )}
        </div>
      </ShowRest>
      {footer}
    </li>
  )
}
