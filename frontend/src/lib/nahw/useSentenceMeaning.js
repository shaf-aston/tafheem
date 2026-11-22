import { useQuery } from '@tanstack/react-query'

import { translateSentence } from '../../api'
import { retryServerErrors } from '../api/apiError'

// The sentence in English, asked of the dictionary as soon as it is analysed:
// the same answer the Dictionary tab gives a sentence. Its word-by-word list is
// also what the chart shows on hover, so the one request serves both.
// Takes the analysis (lib/nahw/analysis), not a raw response.
export function useSentenceMeaning(analysis) {
  const sentence = analysis?.sentence ?? ''
  return useQuery({
    queryKey: ['dictionary-sentence', sentence],
    queryFn: () => translateSentence(sentence),
    enabled: Boolean(sentence),
    staleTime: Infinity,
    // A refusal (429 too many, 422) is not asked again: it answers the same and spends a model call.
    retry: retryServerErrors(1),
  })
}
