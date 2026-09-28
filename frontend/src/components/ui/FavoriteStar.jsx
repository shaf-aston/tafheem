/**
 * Star a hadith, kept in this browser (lib/useHadithFavorites). Its own small
 * file because both the browse list and the search results need it.
 */
export default function FavoriteStar({ on, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={on}
      title={on ? 'Remove from favorites' : 'Add to favorites'}
      className={`shrink-0 leading-none transition-colors ${
        on ? 'text-[var(--warn)]' : 'text-[var(--text-faint)] hover:text-[var(--text-dim)]'
      }`}
    >
      {on ? '★' : '☆'}
    </button>
  )
}
