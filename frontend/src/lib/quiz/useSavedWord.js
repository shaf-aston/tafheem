import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { useSavedState } from '../store/stored'
import { allWordsQuery, coverageQuery } from './quizBanks'
import { SAVED_WORDS, savedEntry, seenAt, tableWordFor } from './savedWords'

/**
 * `{ canSave, saved, toggle }` for one word of the Qur'an reader (lib/quiz/savedWords.js).
 * The word table and coverage are the reader's own cache (useLearntLemmas), so
 * this mostly asks for nothing new; a word from outside the Qur'an is never saved.
 */
export function useSavedWord(word) {
  const quranic = Boolean(seenAt(word) && word?.lemma)
  const words = useQuery({ ...allWordsQuery, enabled: quranic })
  const covering = useQuery({ ...coverageQuery, enabled: quranic })
  const match = useMemo(
    () => (quranic && words.data && covering.data ? tableWordFor(word.lemma, words.data, covering.data) : null),
    [quranic, word, words.data, covering.data],
  )
  const [list, setList] = useSavedState(SAVED_WORDS, [])
  const saved = Boolean(match) && list.some((entry) => entry.lemma === word.lemma)
  const toggle = () => setList((was) => (saved
    ? was.filter((entry) => entry.lemma !== word.lemma)
    : [...was, savedEntry(word, match)]))
  return { canSave: Boolean(match), saved, toggle }
}
