/**
 * Which collection is open, by its short name. Absent while only one is
 * indexed rather than shown as a one-choice control.
 */
import { useHadithCollections } from '../lib/useHadithCollections'

import Segmented from './ui/Segmented'

export default function HadithCollectionPicker({ value, onChange, accent }) {
  const { collections, of } = useHadithCollections()
  if (collections.length <= 1) return null

  return (
    <Segmented
      label="Collection"
      options={collections.map((c) => ({ id: c.id, label: of(c.id).short }))}
      value={value}
      onChange={onChange}
      accent={accent}
      wrap
    />
  )
}
