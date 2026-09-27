/**
 * Surah, ayah and juz as three short selects under the Quran tab's search bar:
 * a way to go somewhere without typing.
 *
 * It follows the place that is open, however it was opened (typed, recent,
 * a search match, another tab), so the row never shows somewhere stale. The
 * surah chosen here is held only until an ayah in it is picked.
 *
 * Styled like the Memorise tab's book and part row: no captions, since each
 * select's choices already say what it is; the words stay as aria-labels.
 */
import { useState } from 'react'

import surahs from '../data/surahs.json'
import { JUZ_COUNT, juzOf, juzStart } from '../lib/juz'

const SELECT = `bg-[var(--surface)] border border-[var(--border)] rounded-[var(--radius-md)]
  px-3 py-1.5 text-sm text-[var(--text)] disabled:opacity-50`

export default function QuranPlacePicker({ surah, ayah, onReadSurah, onOpenAyah }) {
  // The surah in the first select: the open one, until another is picked here.
  const [picked, setPicked] = useState(surah)
  const [followed, setFollowed] = useState(surah)
  if (surah !== followed) { setFollowed(surah); setPicked(surah) }

  const current = picked ? surahs[picked - 1] : null
  const shownAyah = picked && picked === surah ? ayah : null

  const pickSurah = (n) => { setPicked(n); onReadSurah(n) }
  const pickJuz = (n) => { const start = juzStart(n); onOpenAyah(start.surah, start.ayah) }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <select
        aria-label="Surah"
        value={picked ?? ''}
        onChange={(e) => pickSurah(Number(e.target.value))}
        className={`${SELECT} max-w-[16rem]`}
      >
        <option value="" disabled>Surah</option>
        {surahs.map((s) => (
          <option key={s.n} value={s.n}>{s.n}. {s.en} {s.ar}</option>
        ))}
      </select>

      <select
        aria-label="Ayah"
        value={shownAyah ?? ''}
        disabled={!current}
        onChange={(e) => onOpenAyah(picked, Number(e.target.value))}
        className={SELECT}
      >
        <option value="" disabled>Ayah</option>
        {current && Array.from({ length: current.ayahs }, (_, i) => (
          <option key={i + 1} value={i + 1}>Ayah {i + 1}</option>
        ))}
      </select>

      <select
        aria-label="Juz"
        value={picked ? juzOf(picked, shownAyah ?? 1) : ''}
        onChange={(e) => pickJuz(Number(e.target.value))}
        className={SELECT}
      >
        <option value="" disabled>Juz</option>
        {Array.from({ length: JUZ_COUNT }, (_, i) => (
          <option key={i + 1} value={i + 1}>Juz {i + 1}</option>
        ))}
      </select>
    </div>
  )
}
