/**
 * The Quran tab's one view: a whole surah, read, with the ayah being studied
 * beside it. Opening one ayah opens its surah scrolled to it, so the ayah is
 * always read in its place, and the study (AyahStudy) sits in a column to the
 * right, or on a screen too narrow for two columns as a sheet docked under the
 * surah: its handle drags it up to the whole screen or back down.
 *
 * What is read (the text, the English, the recitation) is useSurahReading's;
 * where the reader is in it, and how it moves, is useSurahPlace's. This draws.
 *
 * The request was never the wait. Measured 2026-09-04: both answers were back
 * in 180ms and al-Baqarah appeared at 2,000ms, the rest spent drawing 286 rows
 * before the first could be shown. Two things fix that: the first screen of
 * rows is drawn first (AyahList), and rows off the screen are not laid out
 * (.surah-row).
 */
import { learntWords } from '../../lib/coverage'
import { FIRST_SURAH, LAST_SURAH } from '../../lib/surahRef'
import { useSurahPlace } from '../../lib/useSurahPlace'
import { useSurahReading } from '../../lib/useSurahReading'

import AyahList from './AyahList'
import AyahRail from './AyahRail'
import AyahRow from './AyahRow'
import AyahStudy from './AyahStudy'
import RecitationBar, { Glyph, PLAY } from './RecitationBar'
import SplitBar from './SplitBar'
import { NoTouchButton, ScrollPad } from './NoTouchReading'
import ArabicText from '../ui/ArabicText'
import ReadingOptions from '../ui/ReadingOptions'
import CloseButton from '../ui/CloseButton'
import ErrorAlert from '../ui/ErrorAlert'
import Segmented from '../ui/Segmented'
import Stepper from '../ui/Stepper'
import { Skeleton } from '../ui/Skeleton'
import SourceBadge from '../ui/SourceBadge'

/** The English under one ayah: the chosen translation once it has arrived,
 *  the corpus's word-by-word gloss before that, so nothing is credited to a
 *  book it did not come from. */
const englishFor = (translation, ayah) => (translation.ready ? translation.textFor(ayah.ayah) : ayah.english)

export default function QuranReader({ place, accent, onGo, onPlace, onClose }) {
  const { surah, ayah } = place
  const {
    data, isPending, isError, error, refetch,
    glosses, learnt, allMeanings, showAllMeanings, anyGlosses,
    touch, phone, noTouchButton, showNoTouchButton, noTouchOn, setNoTouch, noTouch,
    reciter, chooseReciter, recitation, reciting, recite, translation,
  } = useSurahReading(surah)
  const {
    twoPanes, stacked, list, here, setHere, tapped, panes, share, setShare,
    goTo, open, shut, changeSurah, swipe, slide, sheet,
  } = useSurahPlace(place, data, onPlace, onClose)

  const study = ayah && (
    <AyahStudy key={`${surah}:${ayah}`} surah={surah} ayah={ayah} onGo={onGo} onClose={shut} accent={accent} sheet={sheet || undefined} />
  )

  // How long the surah is and whose words these are. Beside the name where
  // there is room; a phone keeps its one row of controls and finds these
  // behind the options, so the reading starts higher.
  const about = (
    <>
      {data && <span className="type-small text-[var(--text-faint)] tabular-nums">{data.ayah_count} ayahs</span>}
      {/* The Arabic is the corpus's; the English may not be. Both are named. */}
      {translation.ready && translation.book?.source && <SourceBadge source={translation.book.source} />}
      {data?.source && <SourceBadge source={data.source} />}
    </>
  )

  return (
    <div {...swipe} style={{ '--c': accent }} className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] overflow-clip">
      <header className="flex items-center gap-2 sm:gap-3 flex-wrap p-3 sm:p-4 border-b border-[var(--border)]">
        <Stepper label="surah"
          onPrev={surah > FIRST_SURAH ? () => changeSurah(surah - 1) : null}
          onNext={surah < LAST_SURAH ? () => changeSurah(surah + 1) : null} />
        {data ? (
          <ArabicText size="sm" className="text-[var(--c)]">{data.name_ar}</ArabicText>
        ) : (
          <Skeleton className="h-4 w-24" />
        )}
        {!phone && about}
        <span className="flex-1" />
        {/* Only where there is a choice to make. */}
        {translation.books.length > 1 && (
          <Segmented
            label="Translation"
            options={translation.books.map((book) => ({ id: book.id, label: book.short }))}
            value={translation.chosen}
            onChange={translation.choose}
            accent={accent}
            className="flex-wrap"
          />
        )}
        {data && !reciting && (
          <button type="button" onClick={() => recite.current?.(ayah ?? here)}
            aria-label={`Recite from ${surah}:${ayah ?? here}`} title="Recite"
            className="press tap grid place-items-center w-[var(--layout-chip)] h-[var(--layout-chip)] rounded-full text-[var(--c)] hover:bg-[var(--surface-hi)] transition-colors">
            <Glyph d={PLAY} />
          </button>
        )}
        {touch && noTouchButton && <NoTouchButton on={noTouchOn} onChange={setNoTouch} />}
        <ReadingOptions accent={accent} options={[
          ...(anyGlosses ? [{ label: 'Every word\'s meaning', on: allMeanings, set: showAllMeanings }] : []),
          { label: 'Without-wudu button', on: noTouchButton, set: showNoTouchButton, only: 'touch' },
        ]}>
          {phone && about}
        </ReadingOptions>
        <CloseButton onClick={onClose} aria-label="Close the surah" className="shrink-0" />
      </header>

      {/* Not on a phone: the Surah, Ayah and Juz pickers above already jump to an
          ayah, and the strip cost the reading a row. */}
      {data && !phone && <AyahRail key={`rail ${surah}`} count={data.ayah_count} here={here} open={ayah} onPick={goTo} />}

      {/* Each keyed by the surah to start afresh with it, and each key its own:
          siblings sharing one drew the panes three times on a phone. */}
      <div key={`panes ${surah}`} ref={panes} {...slide}
        className={twoPanes ? 'grid grid-cols-[minmax(0,1fr)_minmax(19rem,26rem)]' : stacked ? 'flex flex-col h-[var(--layout-split)] scroll-mt-14' : ''}>
        <div className={stacked ? 'min-w-0 min-h-0 shrink-0' : 'min-w-0'} style={stacked ? { height: `${share * 100}%` } : undefined}>
          {translation.isError && (
            <div className="p-4" aria-live="assertive">
              <ErrorAlert title="The translation could not be read" error={translation.error} fallback="The Arabic and its word-by-word English are unaffected." onRetry={() => translation.refetch()} />
            </div>
          )}
          {isError && (
            <div className="p-4" aria-live="assertive">
              <ErrorAlert title="Could not open that surah" error={error} fallback="The surah could not be loaded." onRetry={() => refetch()} />
            </div>
          )}
          {isPending && (
            <div className="p-4 space-y-3">
              {Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          )}
          {data && (
            <div className={`flex ${stacked ? 'h-full' : 'h-[var(--layout-pane)]'}`}>
              <AyahList listRef={list} ayahs={data.ayahs} target={ayah === tapped ? null : ayah} still={noTouch} onScrolled={setHere}>
                {(row) => (
                  <AyahRow
                    key={row.ayah}
                    ayah={row}
                    english={englishFor(translation, row)}
                    glosses={glosses?.ayahs?.[row.ayah]}
                    learnt={learntWords(glosses?.lemmas?.[row.ayah], learnt)}
                    allMeanings={allMeanings}
                    src={recitation.urlFor(row.ayah)}
                    segments={recitation.segmentsFor(row.ayah)}
                    open={row.ayah === ayah}
                    onOpen={open}
                  />
                )}
              </AyahList>
              {touch && <ScrollPad list={list} on={noTouch} />}
            </div>
          )}
        </div>
        {twoPanes && (
          <aside aria-label="Study" className="scroll-pane h-[var(--layout-pane)] p-4 border-l border-[var(--border)]">
            {study || (
              <p className="type-small text-[var(--text-faint)]">
                Tap an ayah to study it here: every word's grammar and root, how the words join, and its tafsir.
              </p>
            )}
          </aside>
        )}
        {stacked && (
          <>
            <SplitBar panes={panes} share={share} onShare={setShare} />
            <aside aria-label="Study" className="scroll-pane flex-1 min-h-0 px-4 pb-4 bg-[var(--surface)]">{study}</aside>
          </>
        )}
      </div>

      {data && (
        <RecitationBar
          key={`bar ${surah}`}
          surah={surah}
          count={data.ayah_count}
          from={ayah ?? here}
          here={here}
          recitation={recitation}
          reciter={reciter}
          onReciter={chooseReciter}
          onFollow={goTo}
          startRef={recite}
        />
      )}
    </div>
  )
}
