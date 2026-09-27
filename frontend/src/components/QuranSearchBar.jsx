/**
 * The Qur'an tab's one box: a place ("Nisa 45", "2:255", "النساء ٤٥") or the
 * words themselves ("الحمد لله"), typed or recited.
 *
 * Which of the two a line is, is lib/quranIntent's call; this only draws it and
 * hands the answer back. The line under the box says what Enter will do before
 * it is pressed, so the reading is never a surprise. It is the same SearchBox
 * and MicButton the Dictionary and Daleel use.
 */
import { useMemo } from 'react'

import { hasDiacritics } from '../lib/arabicText'
import { KIND, readQuranQuery } from '../lib/quranIntent'
import { ayahProblem } from '../lib/surahRef'

import ArabicText from './ui/ArabicText'
import MicButton from './ui/MicButton'
import { GoButton } from './ui/RootActions'
import SearchBox from './ui/SearchBox'

export default function QuranSearchBar({ value, onChange, onClear, onOpen, onSearch, onHeard, busy, accent }) {
  const { kind, surahs, ayah, problem } = useMemo(() => readQuranQuery(value), [value])
  const isPlace = kind === KIND.ayah || kind === KIND.surah

  // A place opens only if its ayah exists there; `problem` says so for the first.
  const open = (m) => { if (!ayahProblem(m, ayah)) onOpen(m, ayah) }
  const submit = () => {
    if (kind === KIND.text) onSearch(value.trim())
    else if (!problem && surahs[0]) open(surahs[0])
  }

  return (
    <div className="space-y-3">
      <SearchBox
        id="quran-search"
        label="Surah, ayah or Arabic text"
        hint="Enter to search, or recite it"
        placeholder="Nisa 45, 2:255 or الحمد لله"
        value={value}
        onChange={onChange}
        onSubmit={submit}
        onClear={onClear}
        busy={busy}
        accent={accent}
      >
        <MicButton onHeard={onHeard} match accent={accent} title="Recite an ayah" />
      </SearchBox>

      {problem ? (
        <p className="type-small" style={{ color: 'var(--danger)' }}>{problem}</p>
      ) : (
        kind !== KIND.none && (
          <p className="text-[var(--text-faint)] type-small">
            {kind === KIND.text
              ? 'Enter searches the Qur’an for these words.'
              : kind === KIND.ayah
                ? `Enter opens ${surahs[0].en} ${ayah}.`
                : `Enter reads ${surahs[0].en}.`}
            {kind === KIND.text && hasDiacritics(value) && ' Diacritics are optional; leaving them off matches more.'}
          </p>
        )
      )}

      {/* The words were read, but they are also a surah's exact name: offered
          on the side, never opened by Enter. */}
      {kind === KIND.text && surahs.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {surahs.map((m) => (
            <GoButton key={m.n} onClick={() => onOpen(m, null)} style={{ '--c': accent }}>
              Read surah {m.en}
            </GoButton>
          ))}
        </div>
      )}

      {/* A place: the closest is Enter's, the rest are near misses to pick. */}
      {isPlace && surahs.length > 0 && (
        <ul className="space-y-1.5" aria-label="Matching surahs">
          {surahs.map((m, i) => (
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
