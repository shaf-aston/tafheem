/**
 * "Read the notes" beside a Tamreen question: the notes topics that say they
 * are tested by this exercise. Tamreen renders this but holds no notes data;
 * this asks the notes library itself, cached once either view has asked.
 */
import { useQuery } from '@tanstack/react-query'

import { getNotes } from '../api'

import Chip from './ui/Chip'

export default function NotesLink({ exerciseKey, accent, onOpen }) {
  const { data } = useQuery({ queryKey: ['notes'], queryFn: getNotes, staleTime: Infinity })
  const topics = (data?.topics ?? []).filter((t) => t.tamreen.includes(exerciseKey))
  if (!onOpen || !topics.length) return null
  return topics.map((t) => (
    <Chip key={t.id} accent={accent} title={`Read the notes on ${t.title}`} onClick={() => onOpen(t.id)}>
      Notes: {t.title}
    </Chip>
  ))
}
