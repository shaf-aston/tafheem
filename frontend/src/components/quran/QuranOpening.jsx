/**
 * The Qur'an tab with nothing open: today's ayah to read, then where the
 * reader last stopped. The search box and the wheels follow it in the panel.
 *
 * Today's ayah is only a reference (lib/quran/todayAyah); its Arabic and
 * English are fetched like any other ayah's, so no text is written here.
 * Where you stopped is the journey's last Qur'an place, the same one the tab
 * reopens on, so it is shown only once the reader has been shut.
 */
import { useQuery } from '@tanstack/react-query'

import { lastOn, useJourney } from '../../lib/nav/journey'
import { shareOf } from '../../lib/quiz/coverage'
import { ayahQueries } from '../../lib/quiz/quizAyah'
import surahs from '../../lib/quran/surahs.json'
import { AYAH_REF } from '../../lib/quran/surahRef'
import { todayAyah } from '../../lib/quran/todayAyah'
import { useSurahShare } from '../../lib/quran/useSurahShare'

import ArabicText from '../ui/text/ArabicText'
import Tile from '../ui/display/Tile'
import { Skeleton } from '../ui/feedback/Skeleton'

const nameOf = (surah) => surahs[surah - 1]?.en

export default function QuranOpening({ accent, onOpen }) {
  const { steps, at } = useJourney()
  const stopped = AYAH_REF.exec(lastOn(steps, at, 'quran') ?? '')
  return (
    <div className="space-y-6 md:max-w-2xl">
      <Today accent={accent} onOpen={onOpen} />
      {stopped && <Continue place={{ surah: Number(stopped[1]), ayah: Number(stopped[2]) }} accent={accent} onOpen={onOpen} />}
    </div>
  )
}

function Today({ accent, onOpen }) {
  const place = todayAyah()
  const [arabicQuery, englishQuery] = ayahQueries(place.surah, place.ayah)
  const arabic = useQuery(arabicQuery)
  const english = useQuery(englishQuery)
  // A backend that does not answer leaves the card out, not an empty box.
  if (arabic.isError) return null
  const text = english.data?.passages?.[0]?.text

  return (
    <section aria-label="Today’s ayah" className="space-y-2">
      <h3 className="eyebrow eyebrow-lg">Today</h3>
      {/* Drawn once both have settled, so the card grows once. */}
      {!arabic.data || english.isPending ? (
        <Skeleton className="h-32 w-full" />
      ) : (
        <Tile variant="lead" accent={accent} className="w-full" onClick={() => onOpen(place)}>
          <ArabicText as="p" size="lg" className="text-[var(--text)]">
            {arabic.data.words.map((word) => word.uthmani || word.arabic).join(' ')}
          </ArabicText>
          {text && <p className="type-body text-[var(--text-dim)]">{text}</p>}
          <p className="type-small text-[var(--text-faint)]">
            {nameOf(place.surah)} <span className="font-mono tabular-nums">{place.surah}:{place.ayah}</span>
          </p>
        </Tile>
      )}
    </section>
  )
}

function Continue({ place, accent, onOpen }) {
  const share = useSurahShare(place.surah)
  return (
    <section aria-label="Where you stopped" className="space-y-2">
      <h3 className="eyebrow eyebrow-lg">Continue</h3>
      <Tile variant="chip" accent={accent} className="w-full" onClick={() => onOpen(place)}>
        <span className="min-w-0">
          <span className="block font-semibold">
            {nameOf(place.surah)} <span className="font-mono tabular-nums text-[var(--text-dim)]">{place.surah}:{place.ayah}</span>
          </span>
          {share !== null && (
            <span className="block type-small text-[var(--text-dim)]">You know {shareOf(share, 'en')}% of its words</span>
          )}
        </span>
        <ArabicText size="sm" className="text-[var(--text-dim)]">{surahs[place.surah - 1]?.ar}</ArabicText>
      </Tile>
    </section>
  )
}
