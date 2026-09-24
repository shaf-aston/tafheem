/**
 * A whole surah, for reading rather than studying.
 *
 * One request brings the surah's text and its English, 35ms for al-Baqarah, the
 * longest, because both now come from local databases instead of one network
 * call per ayah. The word-by-word grammar is deliberately NOT fetched here: it is
 * ~2MB for a long surah and is only worth loading for the ayah you stop on, which
 * is what clicking an ayah does.
 *
 * Nothing is cached by hand. react-query keeps the surahs already opened, so
 * paging back and forth costs nothing after the first visit.
 *
 * The request was never the wait. Measured 2026-09-04: both answers were back
 * in 180ms and al-Baqarah appeared at 2,000ms, the rest spent drawing 286 rows
 * before the first could be shown. Two things fix that: the first screen of
 * rows is drawn first (AyahList), and rows off the screen are not laid out
 * (.surah-row).
 */
import { memo, useDeferredValue, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getQuranSurah, getSurahGlosses } from '../api'
import { smartError } from '../lib/apiError'
import { useTranslation } from '../lib/useTranslation'
import { useRecitation } from '../lib/useRecitation'
import { useRecitedWord } from '../lib/useRecitedWord'
import { RECITERS } from '../lib/ayahAudio'
import { useRemembered } from '../lib/useRemembered'

import AyahTafsir from './AyahTafsir'
import ArabicText from './ui/ArabicText'
import ErrorAlert from './ui/ErrorAlert'
import PlayAyah from './ui/PlayAyah'
import RetryButton from './ui/RetryButton'
import Segmented from './ui/Segmented'
import { Skeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'

const FIRST_SURAH = 1
const LAST_SURAH = 114
// Rows drawn before the surah is shown; more than fill the list's first screen.
// The rest are drawn after it is on screen, in a render the browser may
// interrupt, so a long surah appears as fast as a short one.
const FIRST_PAINT_ROWS = 12

/** The English under one ayah, and which book it is really from.
 *
 *  A chosen translation, once its text has arrived, is the only English shown.
 *  Before that, and where no translation is installed at all, the corpus's
 *  word-by-word gloss stands in, and the header badge for the translation is
 *  not drawn, so nothing on screen is credited to a book it did not come from.
 */
function englishFor(translation, ayah) {
  return translation.ready ? translation.textFor(ayah.ayah) : ayah.english
}

/**
 * One ayah, with each word's English shown while the pointer rests on it.
 *
 * Drawing every word in its own box changes nothing about the writing: Arabic
 * joins its letters inside a word and never across a space, so the letters sit
 * exactly as they did when the ayah was one string.
 *
 * `english` missing means the two sources disagreed about how many words this
 * ayah has, or the meanings database was never built. The ayah is then drawn
 * plain, which is the reading view as it always was; a gloss is never guessed
 * onto a word it might not belong to.
 */
function GlossedAyah({ arabic, english, lit = -1 }) {
  const line = 'block text-right leading-loose text-[var(--text)]'
  // Nothing to hover and nothing to light: the ayah is one string again, which
  // is a line of text the browser draws faster than a hundred boxes.
  if (!english && lit < 0) {
    return <ArabicText size="lg" className={line}>{arabic}</ArabicText>
  }

  return (
    <ArabicText size="lg" className={`${line} gloss-line`}>
      {arabic.split(' ').map((word, i) => (
        <span key={i}>
          {i > 0 && ' '}
          <span className={`gloss-word${i === lit ? ' gloss-word-lit' : ''}`}>
            {word}
            {/* lang and dir stated on the English itself: it sits inside a
                right-to-left line, and without them a gloss like "(is) for
                Allah" has its bracket thrown to the wrong end. */}
            {english && (
              <span className="gloss-tip" lang="en" dir="ltr">{english[i]}</span>
            )}
          </span>
        </span>
      ))}
    </ArabicText>
  )
}

/**
 * One ayah of the reading view: its text, its English, and its play button.
 *
 * Its own component because it has to ask which word is being recited, and that
 * question is asked per ayah. A hundred of these are on the page at once, and
 * all but the one sounding answer it with a single comparison.
 */
function AyahRow({ surah, ayah, english, glosses, src, segments, reciter, accent, onOpen }) {
  const lit = useRecitedWord(src, segments)

  return (
    <li className="surah-row">
      <button
        type="button"
        onClick={() => onOpen({ surah, ayah: ayah.ayah })}
        style={{ '--c': accent }}
        className="w-full text-left p-4 flex gap-3 items-start
          hover:bg-[var(--surface-hi)] transition-colors
          focus:outline-none focus:bg-[var(--surface-hi)]"
        title={`Open ${surah}:${ayah.ayah} word by word`}
      >
        <span
          className="shrink-0 mt-1 type-small font-mono rounded-full px-2 py-0.5
            border border-[var(--border)] text-[var(--text-faint)]"
        >
          {ayah.ayah}
        </span>
        <span className="min-w-0 flex-1 space-y-1">
          {/* The display size, not the word size: this is the thing being read,
              and it is the same text the single-ayah view one panel away
              already sets at this size. */}
          <GlossedAyah arabic={ayah.arabic} english={glosses} lit={lit} />
          {/* Once a translation is here it is the only English shown. Falling
              back to the word-by-word gloss for an ayah the book happens to
              skip would put a stitched gloss under that book's name in the
              header. */}
          {/* Ruled off from the Arabic, the way the single-ayah card rules its
              translation off. No tint here: the row tints on hover, and a
              strip that tints as well would read as half the row lighting up.
              Not dimmed either, for the same reason the card is not. */}
          {english && (
            <span className="block type-body text-[var(--text)] leading-relaxed
              border-t border-[var(--border)] pt-2 mt-2">
              {english}
            </span>
          )}
        </span>
      </button>
      {/* Outside the button, not inside it: a button holding another control is
          not something a keyboard or a screen reader can make sense of. Shut,
          so a surah still reads as a surah. */}
      <div className="px-4 pb-3 flex items-start gap-2">
        {/* Not eager here. One ayah's recording is worth fetching before it is
            asked for; 286 of them is a hundred megabytes nobody asked for, so
            these wait for a press, or for the pointer arriving over them. */}
        <PlayAyah surah={surah} ayah={ayah.ayah} reciter={reciter} accent={accent} src={src} />
        <div className="min-w-0 flex-1">
          <AyahTafsir surah={surah} ayah={ayah.ayah} accent={accent} />
        </div>
      </div>
    </li>
  )
}

/**
 * The rows of one surah. Keyed by surah where it is used, so a new surah is a
 * new list: it starts scrolled to the top, and starts again with only the
 * first screen of rows drawn, the rest following once those are on screen.
 */
function AyahList({ ayahs, children: row }) {
  const rows = useDeferredValue(ayahs, ayahs.slice(0, FIRST_PAINT_ROWS))
  return (
    // Capped height with its own scroll: a 286-ayah surah should not push the
    // controls off the top of the page.
    <ol className="max-h-[60vh] overflow-y-auto divide-y divide-[var(--border)]">
      {rows.map(row)}
    </ol>
  )
}

function SurahReader({ surah, accent, onOpenAyah, onChangeSurah, onClose }) {
  // The same remembered voice the single-ayah view uses, by the same key.
  const [reciter] = useRemembered('reciter', RECITERS.map((one) => one.id))

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['quran-surah', surah],
    queryFn: () => getQuranSurah(surah),
    // The Qur'an does not change. Once fetched, keep it for the session.
    staleTime: Infinity,
  })

  // The English of each word, for the hover gloss. Its own request so the text
  // is never held up by it: the surah reads normally while this is in flight,
  // and reads normally for good if it never arrives.
  const { data: glosses } = useQuery({
    queryKey: ['surah-glosses', surah],
    queryFn: () => getSurahGlosses(surah),
    staleTime: Infinity,
  })

  // When each word is recited, so the word being read aloud can be lit. It also
  // decides which recording is played: the times are only true of the file they
  // were measured against.
  const recitation = useRecitation(surah, reciter)

  // A real English sentence per ayah, where a translation has been imported.
  // Falls back to the word-by-word gloss the corpus already carries, which is
  // what this line has always shown.
  const translation = useTranslation(surah)

  // Cycling with the keyboard, since that is the point of a reading view. Ignored
  // while typing, so the surah box above still works normally.
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return
      if (e.target.matches('input, textarea')) return
      if (e.key === 'ArrowLeft' && surah > FIRST_SURAH) onChangeSurah(surah - 1)
      if (e.key === 'ArrowRight' && surah < LAST_SURAH) onChangeSurah(surah + 1)
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [surah, onChangeSurah, onClose])

  return (
    <div className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] overflow-hidden">
      <header className="flex items-center gap-3 flex-wrap p-4 border-b border-[var(--border)]">
        <Stepper
          surah={surah}
          onChange={onChangeSurah}
          accent={accent}
          name={data ? `${data.name_en}` : ''}
        />
        <div className="flex-1 min-w-0">
          {data ? (
            <p className="text-sm text-[var(--text-dim)] truncate">
              {/* Isolated, or the Arabic name reorders the English around it and
                  the line reads "286 · البقرة ayahs". */}
              <ArabicText size="sm" className="text-[var(--text)]" style={{ unicodeBidi: 'isolate' }}>
                {data.name_ar}
              </ArabicText>
              <span className="mx-2">·</span>
              <span style={{ unicodeBidi: 'isolate' }}>{data.ayah_count} ayahs</span>
            </p>
          ) : (
            <Skeleton className="h-4 w-40" />
          )}
        </div>
        {/* Only where there is a choice to make. One translation installed is
            not a picker with one option, it is no picker. */}
        {translation.books.length > 1 && (
          <Segmented
            label="Translation"
            options={translation.books.map((book) => ({ id: book.id, label: book.short }))}
            /* Every translation here is English, so no ArabicText branch: an
               Arabic-script name would need one, as the commentary picker does. */
            value={translation.chosen}
            onChange={translation.choose}
            accent={accent}
            className="flex-wrap"
          />
        )}
        {/* The Arabic is the corpus's; the English line under it may not be.
            Both are named, because a page that shows two sources under one badge
            is a page that is quietly wrong about one of them. */}
        {translation.ready && translation.book?.source && (
          <SourceBadge source={translation.book.source} />
        )}
        {data?.source && <SourceBadge source={data.source} />}
        <button
          type="button"
          onClick={onClose}
          className="text-xs text-[var(--text-faint)] hover:text-[var(--text)] transition-colors px-2 py-1"
        >
          Close
        </button>
      </header>

      {translation.isError && (
        <div className="p-4" aria-live="assertive">
          <ErrorAlert title="The translation could not be read">
            {smartError(translation.error, 'The Arabic and its word-by-word English are unaffected.')}
            <RetryButton onClick={() => translation.refetch()} />
          </ErrorAlert>
        </div>
      )}

      {isError && (
        <div className="p-4" aria-live="assertive">
          <ErrorAlert title="Could not open that surah">
            {smartError(error, 'The surah could not be loaded.')}
            <RetryButton onClick={() => refetch()} />
          </ErrorAlert>
        </div>
      )}

      {isPending && (
        <div className="p-4 space-y-3">
          {Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-12 w-full" />)}
        </div>
      )}

      {data && (
        <>
          <AyahList key={surah} ayahs={data.ayahs}>
            {(ayah) => (
              <AyahRow
                key={ayah.ayah}
                surah={data.surah}
                ayah={ayah}
                english={englishFor(translation, ayah)}
                glosses={glosses?.[ayah.ayah]}
                src={recitation.urlFor(ayah.ayah)}
                segments={recitation.segmentsFor(ayah.ayah)}
                reciter={reciter}
                accent={accent}
                onOpen={onOpenAyah}
              />
            )}
          </AyahList>
          <p className="px-4 py-2 type-small text-[var(--text-faint)] border-t border-[var(--border)]">
            Tap an ayah for its grammar · ← → change surah · Esc closes
          </p>
        </>
      )}
    </div>
  )
}

function Stepper({ surah, onChange, accent, name }) {
  const step = (to) => onChange(Math.min(LAST_SURAH, Math.max(FIRST_SURAH, to)))
  const arrow = `w-7 h-7 rounded-full border border-[var(--border)] text-[var(--text-dim)]
    hover:text-[var(--text)] hover:border-[var(--c)] disabled:opacity-30
    disabled:hover:border-[var(--border)] transition-colors shrink-0`

  return (
    <div className="flex items-center gap-2" style={{ '--c': accent }}>
      <button type="button" className={arrow} onClick={() => step(surah - 1)}
        disabled={surah <= FIRST_SURAH} aria-label="Previous surah">‹</button>
      <span className="font-semibold text-[var(--text)] whitespace-nowrap">
        {surah}. {name || '…'}
      </span>
      <button type="button" className={arrow} onClick={() => step(surah + 1)}
        disabled={surah >= LAST_SURAH} aria-label="Next surah">›</button>
    </div>
  )
}

export default memo(SurahReader)
