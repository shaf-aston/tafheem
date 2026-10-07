/**
 * How much of each surah the learnt words cover, one row per surah.
 *
 * Shut by default, and its file is fetched only once opened: 114 rows is a
 * list for looking things up, not something every quiz visit needs.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { shareOf, surahShares } from '../lib/coverage'
import { surahCoverage, surahList } from '../lib/quizBanks'

import ArabicText from './ui/ArabicText'
import Disclosure from './ui/Disclosure'
import { Skeleton } from './ui/Skeleton'

export default function SurahCoverage({ words, covering, learnt, say, language }) {
  const [open, setOpen] = useState(false)
  const bySurah = useQuery({ queryKey: ['quiz-surah-coverage'], queryFn: surahCoverage, enabled: open })
  const surahs = useQuery({ queryKey: ['quiz-surahs'], queryFn: surahList, enabled: open })
  const shares = useMemo(
    () => (bySurah.data ? surahShares(words, covering, learnt, bySurah.data) : null),
    [words, covering, learnt, bySurah.data],
  )

  return (
    <Disclosure label={say('How much of each surah you know')} onToggle={setOpen}>
      {bySurah.isError || surahs.isError ? (
        <p className="type-small text-[var(--text-faint)]">{say('The surah list can’t be loaded right now.')}</p>
      ) : !shares || !surahs.data ? (
        <Skeleton className="h-24 w-full" />
      ) : (
        <ul className="space-y-2 max-h-80 overflow-y-auto pe-1">
          {surahs.data.map((surah, i) => (
            <li key={surah.id} className="grid grid-cols-[2rem_1fr_3.5rem] items-center gap-3">
              <span className="type-small text-[var(--text-faint)] tabular-nums">{surah.id}</span>
              <span className="min-w-0 space-y-1">
                <span className="flex items-baseline justify-between gap-2">
                  <span className="type-small text-[var(--text-dim)] truncate">{surah.name}</span>
                  <ArabicText size="sm">{surah.arabic}</ArabicText>
                </span>
                <span className="block h-1 rounded-full bg-[var(--surface)] overflow-hidden" aria-hidden="true">
                  <span className="block h-full rounded-full bg-[var(--success)]"
                    style={{ width: `${shares[i] * 100}%` }} />
                </span>
              </span>
              <span className="type-small tabular-nums text-end">{shareOf(shares[i], language)}%</span>
            </li>
          ))}
        </ul>
      )}
    </Disclosure>
  )
}
