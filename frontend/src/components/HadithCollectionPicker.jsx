/**
 * Which collection is open. Absent while only one is indexed (today, just
 * Bukhari) rather than shown as a one-choice control; it appears on its own
 * the moment a second collection is built, no code change needed.
 */
import Segmented from './ui/Segmented'

export default function HadithCollectionPicker({ collections, value, onChange, accent }) {
  if (collections.length <= 1) return null

  return (
    <Segmented
      label="Collection"
      options={collections.map((c) => ({ id: c.id, label: c.name }))}
      value={value}
      onChange={onChange}
      accent={accent}
      wrap
    />
  )
}
