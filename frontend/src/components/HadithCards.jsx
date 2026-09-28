/**
 * A run of hadiths, each with a copy button and a star. One list for a book,
 * for search hits and for the Starred view, so all three behave the same.
 *
 * `collections` is given where hadiths from more than one collection can meet
 * (search, Starred): the label then names the collection as well. A book's own
 * list omits it and passes `collection`, since its rows do not say which.
 */
import { useHadithFavorites } from '../lib/useHadithFavorites'

import CopyButton from './ui/CopyButton'
import FavoriteStar from './ui/FavoriteStar'
import HadithText from './ui/HadithText'

export default function HadithCards({ items, accent, collection, collections }) {
  const { isFavorite, toggle } = useHadithFavorites()
  const nameOf = (id) => collections?.find((c) => c.id === id)?.name ?? id

  return (
    <ul className="list-none m-0 p-0 space-y-2">
      {items.map((item, i) => {
        const h = { ...item, collection: item.collection ?? collection }
        const ref = `${h.number}${h.part ?? ''}`
        return (
          <HadithText
            key={`${h.collection}:${ref}`}
            id={`hadith-${ref}`}
            index={i}
            label={collections ? `${nameOf(h.collection)} ${ref}` : ref}
            arabic={h.arabic}
            english={h.english}
            accent={accent}
            action={(
              <span className="flex items-center gap-2">
                <CopyButton small label="Copy" text={[h.arabic, h.english].filter(Boolean).join('\n\n')} />
                <FavoriteStar on={isFavorite(h)} onClick={() => toggle(h)} />
              </span>
            )}
          />
        )
      })}
    </ul>
  )
}
