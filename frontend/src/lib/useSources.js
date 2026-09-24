/**
 * Every source the app is built on, fetched once and shared.
 *
 * Mirrors useHealth: one query key, so the line at the foot of a tab and the
 * full list in Settings read the same answer rather than asking twice. The
 * wording is the backend's, data/sources.json is the only place a source is
 * described, and nothing here invents or shortens a description.
 *
 * A failure is quiet on purpose. Not knowing where an answer came from is worth
 * saying (see SourceFooter), but it is not worth an error banner over the top
 * of a page that is otherwise working.
 */
import { useQuery } from '@tanstack/react-query'

import { getSources } from '../api'

export function useSources() {
  const { data, isPending, isError } = useQuery({
    queryKey: ['sources'],
    queryFn: getSources,
    staleTime: Infinity,
  })

  return { sources: data ?? [], isPending, isError }
}

/** The sources one tab reads, in the order sources.json lists them. */
export function sourcesFor(sources, tab) {
  return sources.filter((source) => source.used_in?.includes(tab))
}
