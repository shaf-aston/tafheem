/**
 * The words of the hadiths an event is told by, under the event itself.
 *
 * A number and a link were all this tab gave: a reader who wanted to know what
 * the Prophet actually said had to leave the app for sunnah.com and find his
 * way back. The page has the room, so the words sit here, the book's Arabic and
 * the English under it.
 *
 * What was said is drawn apart from what is told about it. The chain of
 * narrators, the scene, who did what next: all of that is the telling, and it
 * is drawn back so the eye lands on the saying. The books mark the saying
 * themselves with quote marks and lib/hadithWords reads that mark; where a book
 * marked nothing, nothing is claimed and the hadith prints in one plain colour.
 * The marks are kept as well as the colour, because a reader who cannot tell
 * two colours apart still has to be able to tell speech from telling.
 *
 * The words come with the library (services/timelines), so an opened event has
 * them already. A cited number with no words is not an error: the tab shows the
 * number alone, as it always did.
 */
import ArabicText from './ui/ArabicText'
import ShowRest from './ui/ShowRest'
import { hadithKey, narrated, saying } from '../lib/hadithWords'
import { themeVariable } from '../theme'

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

function One({ label, words, accent }) {
  const { narrator, body } = narrated(words.english)

  return (
    <li className="rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface-hi)] px-3 py-2.5">
      <p className="type-tiny uppercase tracking-wide text-[var(--text-faint)] m-0">{label}</p>

      <ShowRest lines={LINES} accent={accent} more="Show the rest" less="Show less" className="mt-1.5">
        <ArabicText as="p" size="sm" className="block leading-loose m-0">
          {/* The book's own mark, kept as it is written in Arabic. */}
          <Spans text={words.arabic} marks={['«', '»']} />
        </ArabicText>

        {words.english && (
          <p className="type-ui leading-relaxed mt-2 pt-2 border-t border-[var(--border)] max-w-prose">
            {/* Who is passing it on: named before the words, and drawn back
                with them, because it is not part of what was said. */}
            {narrator && <span style={TONE.told}>{narrator} </span>}
            <Spans text={body} marks={['“', '”']} />
          </p>
        )}
      </ShowRest>
    </li>
  )
}

export default function TimelineHadith({ refs = [], only, library, accent, className = '' }) {
  const told = refs
    .map((ref) => ({ ref, key: hadithKey(ref) }))
    // `only` is what this step is the first to cite (lib/hadithWords printedBy);
    // without it, everything cited here that has words.
    .filter(({ key }) => library.hadith?.[key] && (!only || only.has(key)))
  if (!told.length) return null

  return (
    <ul className={`list-none m-0 p-0 space-y-2 ${className}`.trim()}>
      {told.map(({ ref, key }) => (
        <One
          key={key}
          label={`${library.collections[ref.hadith].name} ${ref.number}${ref.part ?? ''}`}
          words={library.hadith[key]}
          accent={accent}
        />
      ))}
    </ul>
  )
}
