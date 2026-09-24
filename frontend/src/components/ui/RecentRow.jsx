/**
 * A row of "already asked" chips above a search box. Dictionary had this
 * inline; the Qur'an tab needs the same row for ayah references, so it moved
 * here rather than being copied a second time.
 */
import Chip from './Chip'
import { isArabic } from '../../lib/arabicText'

export default function RecentRow({ items, accent, onPick, mono = false, label = 'Recent' }) {
  // The same word twice is one thing looked up twice, not two things. The store
  // above keeps whole records and counts two of them as different if anything
  // else about them differs, so "food" asked on two days arrives here twice; the
  // row showed it twice and handed React the same key for both. Kept in the
  // order they arrived, newest first, so the near duplicate is the one dropped.
  const seen = [...new Set(items ?? [])]
  if (seen.length === 0) return null

  return (
    <div className="recent-row flex flex-wrap gap-1.5 items-center">
      <span className="text-[var(--text-faint)] type-small shrink-0">{label}</span>
      {seen.map((item) => (
        <Chip
          key={item}
          arabic={isArabic(item)}
          accent={accent}
          quiet
          onClick={() => onPick(item)}
        >
          {/* Ayah refs like "2:255" want a fixed-width digit font, prose recents don't. */}
          <span className={mono ? 'font-mono' : undefined}>{item}</span>
        </Chip>
      ))}
    </div>
  )
}
