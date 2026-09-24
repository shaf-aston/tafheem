/**
 * The classical dictionaries on a root, whole, in the books' own words.
 *
 * The card above this one says what the letters have meant in a sentence, in
 * Ibn Faris's words. This is the rest of the shelf: Lisan al-Arab, Taj al-Arus
 * and Lane, each entry printed as its own book printed it, nothing shortened
 * and no two books run together. Ibn Faris himself is not repeated down here;
 * the copy that used to sit on the shelf was the same book without its harakat
 * or its English. One book that returns to a root in a
 * later volume is one card with a break in it, not two cards wearing the same
 * name.
 *
 * Open, with each entry cut to its first lines and the rest a press away. The
 * shelf used to be shut behind a drop-down with every book shut behind another
 * one inside it, which was five presses before a reader saw a single word of a
 * dictionary. Being open is what makes it worth having, so it asks for the
 * books as soon as the root is known. Three entries on a common root run past a
 * hundred kilobytes; that is one call to a dictionary on this machine, and it
 * buys the reader the thing they came for.
 *
 * Lane is the only one in English and is marked as such rather than left for the
 * reader to discover, because "which of these can I actually read" is the first
 * question anyone who cannot read the other two will have.
 */
import { useId, useMemo, useState } from 'react'
import { flushSync } from 'react-dom'
import { useQuery } from '@tanstack/react-query'

import { getLexicons } from '../api'
import { laneEntry } from '../lib/laneEntry'
import { smartError } from '../lib/apiError'
import { scrollToEl } from '../lib/scrollToEl'
import { accentOf } from '../lib/tabs'
import { LANE, LANE_TIDY_LABEL, LANE_TIDY_TITLE, useLaneTidy } from '../lib/useLaneTidy'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import ErrorAlert from './ui/ErrorAlert'
import FlagButton from './ui/FlagButton'
import RetryButton from './ui/RetryButton'
import ShowRest from './ui/ShowRest'
import { Skeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'

/** How the three kinds of nothing are told apart. Never one sentence for all. */
const NOTHING = {
  missing: 'The dictionaries are not built on this machine yet. Run backend/scripts/build_lexicons.py.',
  broken: 'The dictionaries are here but could not be read. The rest of the page is unaffected.',
  ready: 'None of these books has an entry under these letters.',
}

/** Added to that one sentence only, and only when there is another root to try. */
const ELSEWHERE = ' The other root above may be the one they file it under.'

export default function LexiconShelf({ root: asked, hasAlternates }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['lexicons', asked],
    queryFn: () => getLexicons(asked),
    enabled: Boolean(asked),
    staleTime: Infinity,
  })

  if (!asked) return null
  const entries = data?.entries ?? []

  return (
    <section className="rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden">
      <header className="px-4 py-2.5 bg-[var(--surface)] space-y-1">
        <h3 className="text-sm font-medium text-[var(--text)]">
          What the classical dictionaries say: Lisan al-Arab, Taj al-Arus, Lane
        </h3>
      </header>

      <div className="p-4 space-y-3">
        {isPending && <Skeleton className="h-24" />}

        {isError && (
          <ErrorAlert
            title="The dictionaries could not be read"
            message={smartError(error)}
            action={<RetryButton onClick={() => refetch()} />}
          />
        )}

        {data && entries.length === 0 && (
          <Nothing said={NOTHING[data.status] ?? NOTHING.ready} hasAlternates={hasAlternates} />
        )}

        {entries.map((entry) => (
          <BookEntry key={entry.book} entry={entry} root={data.root} />
        ))}
      </div>
    </section>
  )
}

/**
 * Why the shelf is empty. Three reasons, three sentences, never one for all.
 *
 * Only the "no entry" one takes the nudge towards the other root: a book that
 * is not installed is not going to be found under different letters either.
 */
const Nothing = ({ said, hasAlternates }) => (
  <p className="type-small text-[var(--text-faint)]">
    {said}{hasAlternates && said === NOTHING.ready && ELSEWHERE}
  </p>
)

function BookEntry({ entry, root }) {
  const arabic = entry.language === 'ar'
  const lane = entry.book === LANE
  const [tidy, setTidy] = useLaneTidy()
  const [open, setOpen] = useState(false)
  const forms = useMemo(() => (lane ? laneEntry(entry.text, { tidy }) : null), [lane, entry.text, tidy])
  const anchor = useId()
  // Open the fold first, synchronously: a section still under the cut would
  // scroll the clipped box, not the page.
  const jump = (i) => {
    flushSync(() => setOpen(true))
    scrollToEl(document.getElementById(`${anchor}-${i}`), 'top')
  }

  return (
    <article className="rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden">
      <header className="px-3 py-2 bg-[var(--surface)] flex items-baseline gap-2 flex-wrap">
        {arabic
          ? <ArabicText size="sm">{entry.title}</ArabicText>
          : <span className="text-sm text-[var(--text)]">{entry.title}</span>}
        <span className="type-small text-[var(--text-faint)]">
          {entry.author}{entry.died ? `, d. ${entry.died}` : ''}
          {arabic ? '' : ' · in English'}
        </span>
        {/* Only Lane carries the scholar's marks, so only his title has the switch. */}
        {lane && (
          <div className="ms-auto self-center">
            <FlagButton value={tidy} onChange={setTidy} accent={accentOf('dict')} title={LANE_TIDY_TITLE}>
              {LANE_TIDY_LABEL}
            </FlagButton>
          </div>
        )}
      </header>

      <div className="p-3 space-y-2">
        {/* Said before the entry, not after: a reader who typed امر and is shown
            the book's أمر must know that before they read a word of it. */}
        {entry.filed_under && (
          <p className="type-small text-[var(--text-faint)]">
            Nothing under {root}; this is the entry the book files under{' '}
            <ArabicText size="tiny">{entry.filed_under}</ArabicText>.
          </p>
        )}

        {/* A snippet, then the press. The entry used to live in a box with its
            own scrollbar, which hid the same words and also took the wheel off
            the page inside it. How tall the snippet stands is theme.json's
            lexicon.entry-h, the same knob that used to set the box. */}
        {lane && <LaneIndex forms={forms} onJump={jump} />}

        <ShowRest height="var(--lexicon-entry-h)" open={open} onOpenChange={setOpen}>
          {lane
            ? <LaneEntry forms={forms} anchor={anchor} />
            : <ArabicText as="p" size="sm" className="leading-relaxed whitespace-pre-line">{entry.text}</ArabicText>}
        </ShowRest>

        <SourceBadge source={entry.source} />
      </div>
    </article>
  )
}

/**
 * Every headword in the entry, one press from its section. Lane on a common
 * root runs to thousands of words; this is how a reader finds the one they came
 * for without reading down to it. Right to left, like the words themselves.
 */
const LaneIndex = ({ forms, onJump }) => (
  <nav dir="rtl" aria-label="Words in this entry" className="flex flex-wrap gap-1.5">
    {forms.map((form, i) => form.word && (
      <Chip key={i} arabic accent={accentOf('dict')} onClick={() => onJump(i)}
        title={form.form ? `Form ${form.form}` : undefined}>
        {form.word}
      </Chip>
    ))}
  </nav>
)

/** Whether a section has more than one sense, so its first is numbered too. */
const hasSenses = (form) => form.senses.some((sense) => sense.kind === 'sense' && sense.number > 1)

/**
 * Lane's entry, set the way his book sets it: a heading per verb form, the
 * senses numbered under it, the finer points stepped in under those, and the
 * authorities behind every claim held back in grey so the eye can run over
 * them. One run-on paragraph was the same words and unreadable; lib/laneEntry
 * works out the shape, this only draws it.
 */
function LaneEntry({ forms, anchor }) {
  return (
    <div className="space-y-4">
      {forms.map((form, i) => (
        // One headword per section, ruled off from the next. Lane starts a new
        // paragraph at every one and the column read as a single grey slab
        // without it.
        <section
          key={i}
          id={`${anchor}-${i}`}
          className="space-y-2 border-t border-[var(--border)] pt-3 first:border-0 first:pt-0 scroll-mt-24"
        >
          {/* The word leads, so the eye running down the column finds it. */}
          {(form.word || form.form) && (
            <h4 className="flex items-baseline gap-2">
              {form.word && <ArabicText size="base" className="text-[var(--text)]">{form.word}</ArabicText>}
              {form.form && (
                <span className="type-small font-medium text-[var(--text-dim)] uppercase tracking-wide">
                  Form {form.form}
                </span>
              )}
            </h4>
          )}
          {form.senses.map((sense, j) => (
            <p
              key={j}
              // A sub-sense is stepped in and dimmed: it qualifies the sense
              // above. Same size, since on many words it carries the meaning.
              className={sense.kind === 'sub'
                ? 'ps-5 type-body leading-relaxed text-[var(--text-dim)]'
                : 'type-body leading-relaxed text-[var(--text)]'}
            >
              {/* Lane's own numbering, not one invented here. Once a section
                  has a second sense its first is numbered too, so a "2."
                  never stands alone. */}
              {(sense.kind === 'sub' ? sense.number > 1 : sense.number > 0 && hasSenses(form)) && (
                <span className="font-semibold text-[var(--text)] me-1">
                  {sense.kind === 'sub' ? '·' : `${sense.number}.`}
                </span>
              )}
              {sense.pieces.map((piece, k) => (
                <span
                  key={k}
                  // A verse wears the Qur'an tab's own colour, so "Qur'án 8:62"
                  // reads as the same thing there and here.
                  style={piece.kind === 'ref' ? { color: accentOf('quran') } : undefined}
                  className={
                    piece.kind === 'cite'
                      ? 'text-[var(--text-faint)]'
                      : piece.kind === 'tag'
                        ? 'italic text-[var(--text-dim)]'
                        : undefined
                  }
                >
                  {piece.text}
                </span>
              ))}
            </p>
          ))}
        </section>
      ))}
    </div>
  )
}
