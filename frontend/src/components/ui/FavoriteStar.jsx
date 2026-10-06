/**
 * Star a hadith, kept in this browser (lib/useHadithFavorites). Its own small
 * file because the browse list, the search results and the Starred view all
 * need it.
 */
import { useState } from 'react'

export default function FavoriteStar({ on, onClick }) {
  // The swell plays when the star is pressed on, not for every star already on
  // when the list loads.
  const [popped, setPopped] = useState(false)

  return (
    <button
      type="button"
      onClick={() => { setPopped(!on); onClick() }}
      onAnimationEnd={() => setPopped(false)}
      aria-pressed={on}
      title={on ? 'Remove from favorites' : 'Add to favorites'}
      className={`press tap shrink-0 leading-none transition-colors ${popped ? 'pop' : ''} ${
        on ? 'text-[var(--warn)]' : 'text-[var(--text-faint)] hover:text-[var(--text-dim)]'
      }`}
    >
      {on ? '★' : '☆'}
    </button>
  )
}
