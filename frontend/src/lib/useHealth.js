/**
 * One health check, shared by every panel that needs it.
 *
 * It runs once and is cached under a single query key, so the header pill, the
 * dictionary and the Quran panel all read the same answer instead of each
 * asking the backend the same question.
 */
import { useQuery } from '@tanstack/react-query'

import { healthCheck } from '../api'
import { MISSING } from './loadStatus'
import { useSetting } from './settings'

export function useHealth() {
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  })

  return {
    status: isError ? 'error' : isPending ? 'checking' : 'ok',
    nlpEngine: data?.nlp_engine ?? '',
    aiBackend: data?.ai_backend ?? '',
    // Which ear would answer a spoken search. Here for the same reason the AI
    // backend is: an engine that quietly stopped working should be readable,
    // not guessed at from how slow the microphone feels.
    ear: data?.ear ?? '',
    // The trial listening model's name, empty when the server offers none.
    reciteTrial: data?.recite_trial ?? '',
    // Null until the answer arrives, so a panel can tell "not installed" apart
    // from "not asked yet" and stay quiet in the meantime.
    dictionaryLoaded: data ? data.dictionary_loaded === true : null,
    corpusLoaded: data ? data.corpus_loaded === true : null,
    // 'missing' | 'broken' | 'ready', or null before the answer arrives. Three
    // states rather than a flag, because "no book here" and "the book would not
    // read" need different words on screen.
    rootMeaningStatus: data ? (data.root_meaning_status ?? MISSING) : null,
    // A failed health check is not a slow one. Without this a panel waiting on
    // `null` shows its loading bar for ever, with no error and nothing to retry.
    healthFailed: isError,
    retryHealth: refetch,
  }
}

/**
 * Whether a recitation is heard by the trial model: chosen under Settings,
 * Listening, and only while the server still offers one, so a saved choice
 * never outlives the model. Every recitation asks here: Memorise, Grow, checks.
 */
export function useTrial() {
  const { reciteTrial } = useHealth()
  return useSetting('listening-ear') === 'trial' && Boolean(reciteTrial)
}
