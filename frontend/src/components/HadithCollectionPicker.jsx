/**
 * Which collection is open, by its short name. Absent while only one is
 * indexed rather than shown as a one-choice control.
 */
import Segmented from './ui/Segmented'

export default function HadithCollectionPicker({ collections, value, onChange, accent }) {
  if (collections.length <= 1) return null

  return (
    <Segmented
      label="Collection"
      options={collections.map((c) => ({ id: c.id, label: c.short || c.name }))}
      value={value}
      onChange={onChange}
      accent={accent}
      wrap
    />
  )
}
