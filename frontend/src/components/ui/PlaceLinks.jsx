import { useMemo } from 'react'

import { placeProblem, placesNamed } from '../../lib/surahRef'
import { GoButton } from './RootActions'

// "Nisa 45" typed into a tab's search box names an ayah, not a phrase: offer to
// open it. The reading is lib/surahRef's, so every tab agrees on what counts.
export default function PlaceLinks({ query, onGo, accent }) {
  const places = useMemo(() => placesNamed(query), [query])
  if (!onGo) return null
  if (places.length === 0) {
    const problem = placeProblem(query)
    return problem && <p className="type-small text-[var(--text-faint)]">{problem}</p>
  }
  return (
    <div className="flex flex-wrap gap-2">
      {places.map(({ surah, ayah, ref }) => (
        <GoButton key={ref} onClick={() => onGo('quran', ref)} style={{ '--c': accent }}>
          Open {surah.en} {ayah}
        </GoButton>
      ))}
    </div>
  )
}
