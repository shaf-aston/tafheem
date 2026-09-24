/**
 * One box for a place in the Qur'an: "Nisa 45", "kahf", "2:255", "النساء ٤٥".
 *
 * Reading the text is lib/surahRef's job; this only draws what it found and
 * hands the chosen surah and ayah back. Enter opens the closest match, and the
 * others are listed underneath in case the closest is not the one meant.
 */
import { useMemo } from 'react'

import { ayahProblem, readSurahRef } from '../lib/surahRef'

import ArabicText from './ui/ArabicText'
import SearchBox from './ui/SearchBox'

export default function SurahRefBox({ value, onChange, onOpen, busy, accent }) {
  const { matches, ayah } = useMemo(() => readSurahRef(value), [value])
  const typed = value.trim() !== ''

  // The closest match is opened by Enter, but only if its ayah exists there.
  const open = (m) => { if (!ayahProblem(m, ayah)) onOpen(m, ayah) }
  const problem = matches[0] ? ayahProblem(matches[0], ayah) : null

  return (
    <div className="space-y-3">
      <SearchBox
        id="surah-ref"
        label="Surah and ayah"
        hint="Type a name and number, like Nisa 45"
        placeholder="Nisa 45"
        value={value}
        onChange={onChange}
        onSubmit={() => matches[0] && open(matches[0])}
        busy={busy}
        accent={accent}
      />

      {typed && matches.length === 0 && (
        <p className="text-[var(--text-faint)] type-small">
          No surah by that name. Try its English spelling, like Baqarah, or the Arabic.
        </p>
      )}
      {problem && <p className="type-small" style={{ color: 'var(--danger)' }}>{problem}</p>}

      {matches.length > 0 && (
        <ul className="space-y-1.5" aria-label="Matching surahs">
          {matches.map((m, i) => (
            <li key={m.n}>
              <button
                type="button"
                onClick={() => open(m)}
                disabled={Boolean(ayahProblem(m, ayah))}
                style={{ '--i': i, '--c': accent }}
                className="rise-in w-full flex items-center justify-between gap-3 text-left px-3 py-2
                  rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)]
                  hover:border-[var(--c)] transition-colors disabled:opacity-50"
              >
                <span className="flex items-baseline gap-2 min-w-0">
                  <span className="type-tiny text-[var(--text-faint)] font-mono tabular-nums">{m.n}</span>
                  <span className="text-[var(--text)]">{m.en}</span>
                  <ArabicText className="text-[var(--text-dim)]">{m.ar}</ArabicText>
                </span>
                <span className="type-tiny text-[var(--text-faint)] font-mono tabular-nums shrink-0">
                  {ayah === null ? `${m.ayahs} ayahs` : `${m.n}:${ayah}`}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
