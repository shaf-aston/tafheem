/**
 * A run of hadiths, each with its grading, a copy button and a star. One list
 * for a book, for search hits and for the Starred view, so all three behave
 * the same.
 *
 * `collections` is every collection, for names and which are Sahih. A book's
 * own list also passes `collection`, since its rows do not say which; there
 * the label is the number alone, and a Sahih book's cards carry no grading
 * because the green dot by the collection's name says it once for all of them.
 * Without it (search, Starred) hadiths from several collections meet, so the
 * label names the collection and every card carries its grading.
 */
import { useHadithFavorites } from '../lib/useHadithFavorites'

import CopyButton from './ui/CopyButton'
import FavoriteStar from './ui/FavoriteStar'
import GradeMark from './ui/GradeMark'
import HadithText from './ui/HadithText'

export default function HadithCards({ items, accent, collection, collections, columns = false, hideChain = false }) {
  const { isFavorite, toggle } = useHadithFavorites()
  const of = (id) => collections.find((c) => c.id === id)

  return (
    <ul className={`list-none m-0 p-0 ${columns ? 'grid gap-2 items-start md:grid-cols-2' : 'space-y-2'}`}>
      {items.map((item, i) => {
        const h = { ...item, collection: item.collection ?? collection }
        const ref = `${h.number}${h.part ?? ''}`
        return (
          <HadithText
            key={`${h.collection}:${ref}`}
            id={`hadith-${ref}`}
            index={i}
            label={collection ? ref : `${of(h.collection)?.short || h.collection} ${ref}`}
            arabic={h.arabic}
            english={h.english}
            accent={accent}
            hideChain={hideChain}
            action={(
              <span className="flex items-center gap-2">
                {!(collection && of(collection)?.sahih) && (
                  <GradeMark grades={h.grades} sahihBy={of(h.collection)?.sahih ? of(h.collection).name : null} cite={h.cite} />
                )}
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
