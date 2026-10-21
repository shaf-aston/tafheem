/**
 * One hadith's own words: Arabic and English, the chain of narrators drawn back.
 *
 * Promoted out of TimelineHadith, which drew this the same way for the
 * hadiths a timeline event cites; the Hadith tab's browse and search both
 * need the identical rendering for a hadith found a different way. One
 * implementation, not two that would drift the moment either was touched.
 *
 * One rule, as sunnah.com draws it: the chain is quiet, what it carries is in
 * full ink. The split is the server's own (`cut`), and the English's
 * "Narrated X:" line is quiet the same way. Nothing guesses who is speaking
 * (lib/hadithWords says why), and the book's own quote marks stand as printed.
 */
import ArabicText from './ArabicText'
import ShowRest from './ShowRest'
import { chainAndBody, narrated } from '../../lib/hadithWords'
import { runs, told, withoutMarks } from '../../lib/rijal'

import NarratorLink from './NarratorLink'
import { themeVariable } from '../../theme'

// The chain and the English's teller line: read past rather than read (theme.json hadith.chain).
const QUIET = 'text-[var(--hadith-chain)]'
// How much of one hadith shows before the rest waits behind a press.
const LINES = Number(themeVariable('--hadith-lines')) || 7
// Cards past this many appear together, so a long book never waits on its own stagger.
const STAGGER_CAP = Number(themeVariable('--hadith-stagger-cap')) || 8
// Where the English sits. A phone: on top, ruled off from the Arabic. A wide screen: the left
// column when split, else under the Arabic as it always was (two columns, the timelines).
const SPLIT = 'order-first mb-3 pb-3 border-b md:m-0 md:p-0 md:border-b-0'
const STACKED = 'max-md:order-first max-md:mb-3 max-md:pb-3 max-md:border-b md:mt-3 md:pt-3 md:border-t'

/**
 * The Arabic, its chain quiet up to `from` (where the body starts; null, all body).
 * `names` are [start, end, id] slices of `text`; each is a ui/NarratorLink.
 */
function Spans({ text, names = [], onNarrator, from = null }) {
  // chainAndBody drops the direction marks, so the slices move with them.
  const at = withoutMarks(text, names)
  let start = 0
  return chainAndBody(text, from).map((part) => {
    const parts = runs(part.text, at, start).map((run, j) => (
      <NarratorLink key={j} id={run.id} onOpen={onNarrator}>{run.text}</NarratorLink>
    ))
    start += part.text.length
    return <span key={part.kind} className={part.kind === 'chain' ? QUIET : undefined}>{parts}</span>
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
 * `split` sets English left and Arabic right on a wide screen, as sunnah.com does; a phone stacks them, English on top.
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
          className="type-tiny tabular-nums whitespace-nowrap min-w-7 h-7 px-2 grid place-items-center rounded-full border"
        >
          {label}
        </span>
        {action}
      </div>

      <ShowRest lines={LINES} accent={accent} more="Show the rest" less="Show less">
        {/* A phone puts the English first, as sunnah.com does: Arabic first, its cut showed only the
            chain of narrators and the meaning waited behind "Show the rest". */}
        <div className={`flex flex-col ${split && english ? 'md:grid md:grid-cols-2 md:gap-x-8 md:items-start' : ''}`}>
        <ArabicText as="p" size="base" className="block leading-loose m-0">
          <Spans text={shown.text} names={shown.names} onNarrator={onNarrator} from={from} />
        </ArabicText>

        {english && (
          <p className={`type-ui leading-relaxed border-[var(--border)] ${split ? SPLIT : STACKED}`}>
            {narrator && <span className={QUIET}>{narrator} </span>}
            {body}
          </p>
        )}
        </div>
      </ShowRest>
      {footer}
    </li>
  )
}
