/**
 * Surah, ayah and juz as three wheels (ui/WheelPicker) under the Quran tab's search bar:
 * a way to go somewhere without typing.
 *
 * It follows the place that is open, however it was opened (typed, recent,
 * a search match, another tab), so the row never shows somewhere stale. The
 * surah chosen here is held only until an ayah in it is picked.
 *
 * Type in a wheel to spin it: a name or a number.
 */
import { useState } from 'react'

import surahs from '../data/surahs.json'
import { JUZ_COUNT, juzOf, juzStart } from '../lib/juz'
import WheelPicker from './ui/WheelPicker'

export default function QuranPlacePicker({ surah, ayah, accent, onReadSurah, onOpenAyah }) {
  // The surah in the first select: the open one, until another is picked here.
  const [picked, setPicked] = useState(surah)
  const [followed, setFollowed] = useState(surah)
  if (surah !== followed) { setFollowed(surah); setPicked(surah) }

  const current = picked ? surahs[picked - 1] : null
  const shownAyah = picked && picked === surah ? ayah : null

  const pickSurah = (n) => { setPicked(n); onReadSurah(n) }
  const pickJuz = (n) => { const start = juzStart(n); onOpenAyah(start.surah, start.ayah) }

  const surahOptions = surahs.map((s) => ({ value: s.n, label: `${s.n}. ${s.en}`, hint: s.ar, keys: [s.ar] }))
  const ayahOptions = current ? Array.from({ length: current.ayahs }, (_, i) => ({ value: i + 1, label: `Ayah ${i + 1}` })) : []
  const juzOptions = Array.from({ length: JUZ_COUNT }, (_, i) => ({ value: i + 1, label: `Juz ${i + 1}` }))

  return (
    <div className="flex flex-wrap items-center gap-2">
      <WheelPicker label="Surah" placeholder="Surah" options={surahOptions} value={picked} onPick={pickSurah} accent={accent} className="max-w-[16rem]" />
      <WheelPicker label="Ayah" placeholder="Ayah" options={ayahOptions} value={shownAyah} disabled={!current} narrow accent={accent} onPick={(n) => onOpenAyah(picked, n)} />
      <WheelPicker label="Juz" placeholder="Juz" options={juzOptions} narrow accent={accent} value={picked ? juzOf(picked, shownAyah ?? 1) : null} onPick={pickJuz} />
    </div>
  )
}
